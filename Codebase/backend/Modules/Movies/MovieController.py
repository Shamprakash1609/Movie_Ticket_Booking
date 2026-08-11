from Modules.Movies.MovieService import MovieService
from Modules.Movies.MovieModel import Movie
from Modules.Movies.MovieView import MovieView
from Modules.Movies.Strategies import (
    SearchByTitleStrategy,
    SearchByGenreStrategy,
    SearchByLanguageStrategy,
)
from Modules.Common.Exceptions import MovieTicketSystemError
from Modules.Common.Helpers import Helpers


class MovieController:
    def __init__(self):
        self.movie_service = MovieService()

    def add_movie(self, admin_id):
        print("\n--- Add New Movie ---")
        print("(Note: Type 'c' or 'cancel' at any prompt to cancel adding movie)")

        title = Helpers.prompt_non_empty("Title (e.g., Inception): ")
        if not title:
            return

        description = Helpers.prompt_non_empty("Description / Synopsis: ")
        if not description:
            return

        duration = Helpers.prompt_int("Duration in minutes (e.g., 148): ", min_val=1)
        if duration is None:
            return

        genre = Helpers.prompt_non_empty("Genre (e.g., Sci-Fi, Action): ")
        if not genre:
            return

        language = Helpers.prompt_non_empty("Language (e.g., English): ")
        if not language:
            return

        release_date = Helpers.prompt_date(
            "Release Date (YYYY-MM-DD, e.g., 2026-08-15): "
        )
        if not release_date:
            return

        movie = Movie(
            movie_id=None,
            title=title,
            description=description,
            duration=duration,
            genre=genre,
            language=language,
            release_date=release_date,
            rating=0.0,
            poster_url=None,
            created_by=admin_id,
        )

        try:
            self.movie_service.add_movie(movie)
            print(f"\n[Success] Movie '{title}' ({duration} mins) added successfully!")
        except MovieTicketSystemError as e:
            print(f"\n[Error] {str(e)}")

    def view_movies_admin(self):
        print("\n--- View/Search Movies ---")
        print("1. View All")
        print("2. Search by Title")
        print("3. Search by Genre")

        choice = input("Choice: ").strip()
        movies = []

        if choice == "1":
            movies = self.movie_service.get_all_movies()
        elif choice == "2":
            query = Helpers.prompt_non_empty("Enter Title keyword: ")
            if not query:
                return
            movies = self.movie_service.search_movies(SearchByTitleStrategy(), query)
        elif choice == "3":
            query = Helpers.prompt_non_empty("Enter Genre (e.g., Action): ")
            if not query:
                return
            movies = self.movie_service.search_movies(SearchByGenreStrategy(), query)
        else:
            print("[Error] Invalid choice.")
            return

        MovieView.display_movies_table(movies)

    def update_movie(self, admin_id):
        print("\n--- Update Movie ---")
        movie_id = Helpers.prompt_int(
            "Enter Movie ID to update (or 'c' to cancel): ", min_val=1
        )
        if movie_id is None:
            return

        movie = self.movie_service.get_movie(movie_id)
        if not movie:
            print("[Error] Movie not found.")
            return

        print("\nPress Enter to keep existing value.")
        new_title = input(f"Title [{movie.title}]: ").strip() or movie.title
        new_desc = (
            input(f"Description [{movie.description}]: ").strip() or movie.description
        )

        while True:
            new_dur_str = input(f"Duration in minutes [{movie.duration}]: ").strip()
            if not new_dur_str:
                new_duration = movie.duration
                break
            try:
                new_duration = int(new_dur_str)
                if new_duration > 0:
                    break
                print("[Input Error] Duration must be a positive integer in minutes.")
            except ValueError:
                print(
                    "[Input Error] Invalid input. Please enter movie duration as an integer in minutes (e.g., 120)."
                )

        new_genre = input(f"Genre [{movie.genre}]: ").strip() or movie.genre
        new_lang = input(f"Language [{movie.language}]: ").strip() or movie.language

        while True:
            new_date = input(
                f"Release Date YYYY-MM-DD [{movie.release_date}]: "
            ).strip()
            if not new_date:
                new_date = movie.release_date
                break
            if Helpers.is_valid_date(new_date):
                break
            print(
                "[Input Error] Invalid date format. Must be YYYY-MM-DD (e.g., 2026-08-15)."
            )

        updated_movie = Movie(
            movie_id=movie.movie_id,
            title=new_title,
            description=new_desc,
            duration=new_duration,
            genre=new_genre,
            language=new_lang,
            release_date=new_date,
            rating=movie.rating,
            poster_url=movie.poster_url,
            created_by=movie.created_by,
        )

        try:
            self.movie_service.update_movie(updated_movie, admin_id)
            print("[Success] Movie updated successfully.")
        except MovieTicketSystemError as e:
            print(f"[Error] {str(e)}")

    def delete_movie(self, admin_id):
        print("\n--- Delete Movie ---")
        movie_id = Helpers.prompt_int("Enter Movie ID to delete: ", min_val=1)
        if movie_id is None:
            return

        movie = self.movie_service.get_movie(movie_id)
        if not movie:
            print("[Error] Movie not found.")
            return

        confirm = input(
            f"Are you sure you want to delete '{movie.title}'? [y/N]: "
        ).strip()
        if confirm.lower() == "y":
            try:
                self.movie_service.delete_movie(movie_id, admin_id)
                print("[Success] Movie deleted successfully.")
            except MovieTicketSystemError as e:
                print(f"[Error] {str(e)}")
        else:
            print("Deletion cancelled.")

    def browse_movies_customer(self):
        print("\n--- Browse Movies ---")
        print("1. All Movies")
        print("2. Filter by Language")
        print("3. Filter by Genre")

        choice = input("Choice: ")
        movies = []

        if choice == "1":
            movies = self.movie_service.get_all_movies()
        elif choice == "2":
            lang = input("Enter Language: ")
            movies = self.movie_service.search_movies(SearchByLanguageStrategy(), lang)
        elif choice == "3":
            genre = input("Enter Genre: ")
            movies = self.movie_service.search_movies(SearchByGenreStrategy(), genre)
        else:
            print("[Error] Invalid choice.")
            return

        MovieView.display_movie_cards(movies)
