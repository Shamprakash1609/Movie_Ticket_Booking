from Modules.Movies.MovieModel import Movie
from Modules.Common.Helpers import Helpers


class MovieView:
    @staticmethod
    def display_movies_table(movies):
        headers = ["ID", "Title", "Genre", "Duration", "Language", "Rating"]
        rows = []
        for m in movies:
            rows.append(
                [
                    m.movie_id,
                    m.title[:20] + "..." if len(m.title) > 20 else m.title,
                    m.genre,
                    f"{m.duration} mins",
                    m.language,
                    f"{m.rating:.1f}",
                ]
            )
        Helpers.print_table(headers, rows)

    @staticmethod
    def display_movie_cards(movies):
        if not movies:
            print("No movies found.")
            return

        for m in movies:
            print("-" * 40)
            print(f"🎬 {m.title.upper()} ({m.release_date})")
            print(f"⭐ Rating: {m.rating} | ⏱ Duration: {m.duration} mins")
            print(f"🎭 Genre: {m.genre} | 🗣 Language: {m.language}")
            print(f"📝 {m.description}")
            if m.poster_url:
                print(f"🖼 Poster: {m.poster_url}")
            print("-" * 40)
