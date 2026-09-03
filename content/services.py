import os

import requests

TMDB_API_ROOT = 'https://api.themoviedb.org/3'
TMDB_IMAGE_ROOT = 'https://image.tmdb.org/t/p/w500'


def _tmdb_request(path):
    read_token = os.getenv('TMDB_READ_ACCESS_TOKEN', '').strip()
    api_key = os.getenv('TMDB_API_KEY', '').strip()
    if not read_token and not api_key:
        return []

    try:
        timeout = float(os.getenv('TMDB_TIMEOUT_SECONDS', '5'))
        request_kwargs = {'timeout': timeout}
        if read_token:
            request_kwargs['headers'] = {
                'Authorization': f'Bearer {read_token}',
                'accept': 'application/json',
            }
        else:
            request_kwargs['params'] = {'api_key': api_key}

        response = requests.get(
            f'{TMDB_API_ROOT}{path}',
            **request_kwargs,
        )
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
    year = None
    if date_value and len(date_value) >= 4 and date_value[:4].isdigit():
        year = int(date_value[:4])

    poster_path = item.get('poster_path')
    rating = item.get('vote_average')

    return {
        'id': f'tmdb_{content_type}_{item_id}',
        'title': title or 'Untitled',
        'genre': 'TV' if is_tv else 'Movie',
        'thumbnail': f'{TMDB_IMAGE_ROOT}{poster_path}' if poster_path else '',
        'url': f'https://www.themoviedb.org/{"tv" if is_tv else "movie"}/{item_id}',
        'source_type': 'tmdb',
        'content_type': content_type,
        'description': item.get('overview', ''),
        'release_year': year,
        'rating': round(float(rating), 1) if rating is not None else None,
        'external_source': 'tmdb',
        'external_id': str(item_id),
        'is_external': True,
    }


def _fetch_tmdb(path, content_type):
    normalized = []
    for item in _tmdb_request(path):
        result = _normalize_tmdb_item(item, content_type)
        if result:
            normalized.append(result)
    return normalized


def fetch_trending_movies():
    return _fetch_tmdb('/trending/movie/week', 'movie')


def fetch_trending_tv():
    return _fetch_tmdb('/trending/tv/week', 'tv')
