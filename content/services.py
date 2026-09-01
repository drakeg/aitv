import requests

TMDB_API_KEY = "YOUR_API_KEY"


def fetch_trending_movies():
    url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}"
    response = requests.get(url).json()

    movies = []

    for movie in response.get("results", []):
        poster_path = movie.get("poster_path")

        movies.append({
            "id": f"tmdb_{movie['id']}",
            "title": movie.get("title"),
            "genre": "Movie",
            "thumbnail": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else "",
            "url": f"https://www.themoviedb.org/movie/{movie['id']}",
            "source_type": "movie",
            "is_external": True,   # 🔥 important flag
        })

    return movies