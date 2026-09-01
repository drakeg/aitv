import os

import requests

TMDB_TRENDING_URL = 'https://api.themoviedb.org/3/trending/movie/week'


def fetch_trending_movies():
    api_key = os.getenv('TMDB_API_KEY', '').strip()
    if not api_key:
        return []

    try:
        timeout = float(os.getenv('TMDB_TIMEOUT_SECONDS', '5'))
        response = requests.get(
            TMDB_TRENDING_URL,
            params={'api_key': api_key},
            timeout=timeout,
        )
        response.raise_for_status()
        results = response.json().get('results', [])
    except (requests.RequestException, ValueError):
        return []

    movies = []
    for movie in results:
        movie_id = movie.get('id')
        if movie_id is None:
            continue

        poster_path = movie.get('poster_path')
        movies.append({
            'id': f'tmdb_{movie_id}',
            'title': movie.get('title'),
            'genre': 'Movie',
            'thumbnail': (
                f'https://image.tmdb.org/t/p/w500{poster_path}'
                if poster_path else ''
            ),
            'url': f'https://www.themoviedb.org/movie/{movie_id}',
            'source_type': 'movie',
            'is_external': True,
        })

    return movies
