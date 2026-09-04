import os

import requests
from django.conf import settings
from django.core.mail import send_mail

TMDB_API_ROOT = 'https://api.themoviedb.org/3'


def _timeout():
    try:
        return float(os.getenv('SOURCE_TIMEOUT_SECONDS', os.getenv('TMDB_TIMEOUT_SECONDS', '5')))
    except ValueError:
        return 5.0


def fetch_latest_release(content):
    """Return the latest aired release marker for a saved TV title.

    The current implementation supports TMDB-backed TV watchlist entries. Unsupported
    sources return None so the caller can safely skip them without inventing data.
    """
    if content.content_type != 'tv' or content.external_source != 'tmdb' or not content.external_id.isdigit():
        return None

    read_token = os.getenv('TMDB_READ_ACCESS_TOKEN', '').strip()
    api_key = os.getenv('TMDB_API_KEY', '').strip()
    if not read_token and not api_key:
        return None

    headers = None
    params = {}
    if read_token:
        headers = {'Authorization': f'Bearer {read_token}', 'accept': 'application/json'}
    else:
        params['api_key'] = api_key

    try:
        response = requests.get(
            f'{TMDB_API_ROOT}/tv/{content.external_id}',
            params=params,
            headers=headers,
            timeout=_timeout(),
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    episode = data.get('last_episode_to_air') or {}
    season = episode.get('season_number')
    number = episode.get('episode_number')
    air_date = str(episode.get('air_date') or '').strip()
    if season is None or number is None or not air_date:
        return None

    episode_name = str(episode.get('name') or '').strip()
    label = f'S{season} E{number}'
    event_key = f'tmdb-tv:{content.external_id}:{label}:{air_date}'
    message = f'{content.title} released {label} on {air_date}.'
    if episode_name:
        message = f'{content.title} released {label} — {episode_name} on {air_date}.'

    return {
        'event_key': event_key,
        'title': f'New episode: {content.title}',
        'message': message,
        'target_url': content.url,
    }


def send_release_email(user, notification):
    """Send email only when SMTP delivery is explicitly configured."""
    if not getattr(settings, 'RELEASE_EMAIL_CONFIGURED', False) or not user.email:
        return False
    send_mail(
        subject=notification.title,
        message=notification.message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return True
