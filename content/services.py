import os
from html import unescape

import requests

from .providers import detect_provider

TMDB_API_ROOT = 'https://api.themoviedb.org/3'
TMDB_IMAGE_ROOT = 'https://image.tmdb.org/t/p/w500'
TVMAZE_API_ROOT = 'https://api.tvmaze.com'
ARCHIVE_SEARCH_URL = 'https://archive.org/advancedsearch.php'

TMDB_GENRES = {
    28: 'Action', 12: 'Adventure', 16: 'Animation', 35: 'Comedy', 80: 'Crime',
    99: 'Documentary', 18: 'Drama', 10751: 'Family', 14: 'Fantasy', 36: 'History',
    27: 'Horror', 10402: 'Music', 9648: 'Mystery', 10749: 'Romance',
    878: 'Science Fiction', 10770: 'TV Movie', 53: 'Thriller', 10752: 'War',
    37: 'Western', 10759: 'Action & Adventure', 10762: 'Kids', 10763: 'News',
    10764: 'Reality', 10765: 'Sci-Fi & Fantasy', 10766: 'Soap', 10767: 'Talk',
    10768: 'War & Politics',
}
NEWS_TERMS = {'news', 'current affairs'}


def _timeout():
    try:
        return float(os.getenv('SOURCE_TIMEOUT_SECONDS', os.getenv('TMDB_TIMEOUT_SECONDS', '5')))
    except ValueError:
        return 5.0


def _tmdb_request(path):
    read_token = os.getenv('TMDB_READ_ACCESS_TOKEN', '').strip()
    api_key = os.getenv('TMDB_API_KEY', '').strip()
    if not read_token and not api_key:
        return []
    try:
        request_kwargs = {'timeout': _timeout()}
        if read_token:
            request_kwargs['headers'] = {'Authorization': f'Bearer {read_token}', 'accept': 'application/json'}
        else:
            request_kwargs['params'] = {'api_key': api_key}
        response = requests.get(f'{TMDB_API_ROOT}{path}', **request_kwargs)
        response.raise_for_status()
        return response.json().get('results', [])
    except (requests.RequestException, ValueError):
        return []


def _normalize_tmdb_item(item, content_type):
    item_id = item.get('id')
    if item_id is None:
        return None
    is_tv = content_type == 'tv'
    title = item.get('name') if is_tv else item.get('title')
    date_value = item.get('first_air_date') if is_tv else item.get('release_date')
    year = int(date_value[:4]) if date_value and len(date_value) >= 4 and date_value[:4].isdigit() else None
    poster_path = item.get('poster_path')
    rating = item.get('vote_average')
    genres = [TMDB_GENRES[g] for g in item.get('genre_ids', []) if g in TMDB_GENRES]
    genre = ', '.join(genres) or ('TV' if is_tv else 'Movie')
    return {
        'id': f'tmdb_{content_type}_{item_id}', 'title': title or 'Untitled', 'genre': genre,
        'genres': genres, 'thumbnail': f'{TMDB_IMAGE_ROOT}{poster_path}' if poster_path else '',
        'url': f'https://www.themoviedb.org/{"tv" if is_tv else "movie"}/{item_id}',
        'details_url': f'https://www.themoviedb.org/{"tv" if is_tv else "movie"}/{item_id}',
        'source_type': 'tmdb', 'content_type': content_type, 'description': item.get('overview', ''),
        'release_year': year, 'rating': round(float(rating), 1) if rating is not None else None,
        'external_source': 'tmdb', 'external_id': str(item_id), 'is_external': True,
        'is_news': any(name.lower() in NEWS_TERMS for name in genres),
    }


def _fetch_tmdb(path, content_type):
    return [result for item in _tmdb_request(path) if (result := _normalize_tmdb_item(item, content_type))]


def fetch_trending_movies():
    return _fetch_tmdb('/trending/movie/week', 'movie')


def fetch_trending_tv():
    return _fetch_tmdb('/trending/tv/week', 'tv')


def _strip_html(value):
    if not value:
        return ''
    text = str(value)
    while '<' in text and '>' in text:
        start = text.find('<')
        end = text.find('>', start)
        if end == -1:
            break
        text = f'{text[:start]} {text[end + 1:]}'
    return ' '.join(unescape(text).split())


def fetch_live_tv_schedule(limit=40):
    try:
        response = requests.get(f'{TVMAZE_API_ROOT}/schedule', params={'country': 'US'}, timeout=_timeout())
        response.raise_for_status()
        episodes = response.json()
    except (requests.RequestException, ValueError):
        return []

    items = []
    seen = set()
    for episode in episodes:
        show = episode.get('show') or {}
        show_id = show.get('id')
        official_url = (show.get('officialSite') or '').strip()
        if not show_id or not official_url or show_id in seen:
            continue
        network_data = show.get('network') or show.get('webChannel') or {}
        network = (network_data.get('name') or 'TV').strip()
        image = show.get('image') or episode.get('image') or {}
        provider = detect_provider(official_url)
        access_type = provider['access_type'] if provider else 'other'
        provider_name = provider['provider'] if provider else network
        if access_type == 'auth':
            action_label = f'{provider_name} · Sign-in required'
        elif access_type == 'subscription':
            action_label = f'{provider_name} · Subscription'
        else:
            action_label = f'Watch on {provider_name}'
        season, number = episode.get('season'), episode.get('number')
        episode_label = f'S{season} E{number}' if season is not None and number is not None else ''
        genres = [str(value) for value in (show.get('genres') or [])]
        show_type = (show.get('type') or '').strip()
        if show_type and show_type not in genres:
            genres.append(show_type)
        is_news = show_type.lower() in NEWS_TERMS or any(str(g).lower() in NEWS_TERMS for g in genres)
        items.append({
            'id': f'tvmaze_{show_id}', 'title': show.get('name') or 'Untitled',
            'genre': ', '.join(genres) or 'TV', 'genres': genres,
            'thumbnail': image.get('medium') or image.get('original') or '', 'url': official_url,
            'details_url': show.get('url') or '', 'source_type': 'tvmaze', 'content_type': 'tv',
            'description': _strip_html(show.get('summary')),
            'release_year': int(show['premiered'][:4]) if str(show.get('premiered') or '')[:4].isdigit() else None,
            'rating': (show.get('rating') or {}).get('average'), 'external_source': 'tvmaze',
            'external_id': str(show_id), 'is_external': True, 'is_live_source': True,
            'provider': provider_name, 'network': network, 'access_type': access_type,
            'action_label': action_label, 'episode_label': episode_label,
            'airtime': episode.get('airtime') or '', 'runtime': episode.get('runtime'),
            'show_type': show_type, 'is_news': is_news,
        })
        seen.add(show_id)
        if len(items) >= limit:
            break
    return items


def fetch_free_archive_movies(limit=10):
    params = {'q': 'mediatype:movies AND collection:feature_films', 'fl[]': ['identifier', 'title', 'description', 'year'], 'rows': limit, 'page': 1, 'output': 'json', 'sort[]': 'downloads desc'}
    try:
        response = requests.get(ARCHIVE_SEARCH_URL, params=params, timeout=_timeout())
        response.raise_for_status()
        docs = response.json().get('response', {}).get('docs', [])
    except (requests.RequestException, ValueError):
        return []
    items = []
    for doc in docs:
        identifier, title = str(doc.get('identifier') or '').strip(), str(doc.get('title') or '').strip()
        if not identifier or not title:
            continue
        year = doc.get('year')
        if isinstance(year, list): year = year[0] if year else None
        try: year = int(year) if year else None
        except (TypeError, ValueError): year = None
        description = doc.get('description') or ''
        if isinstance(description, list): description = ' '.join(str(part) for part in description)
        items.append({'id': f'archive_{identifier}', 'title': title, 'genre': 'Free Movie', 'genres': [], 'thumbnail': f'https://archive.org/services/img/{identifier}', 'url': f'https://archive.org/details/{identifier}', 'details_url': f'https://archive.org/details/{identifier}', 'source_type': 'internet_archive', 'content_type': 'movie', 'description': _strip_html(description), 'release_year': year, 'rating': None, 'external_source': 'internet_archive', 'external_id': identifier, 'is_external': True, 'is_live_source': True, 'provider': 'Internet Archive', 'network': '', 'access_type': 'free', 'action_label': 'Watch free on Internet Archive', 'is_news': False})
    return items
