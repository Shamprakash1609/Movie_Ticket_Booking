from Modules.Showtimes.ShowtimeService import ShowtimeService
from Modules.Movies.MovieService import MovieService
from Modules.Theaters.TheaterService import TheaterService
from Modules.Movies.MovieView import MovieView
from Modules.Common.Exceptions import MovieTicketSystemError
from Modules.Common.Helpers import Helpers


class ShowtimeController:
    def __init__(self):
        self.showtime_service = ShowtimeService()
        self.movie_service = MovieService()
        self.theater_service = TheaterService()

    def add_showtime(self, admin_id):
        print("\n--- Manage Showtimes (Add) ---")

        movies = self.movie_service.get_all_movies()
        if not movies:
            print("No movies available. Add a movie first.")
            return

        print("\nAvailable Movies:")
        MovieView.display_movies_table(movies)

    def add_showtime(self, admin_id):
        print("\n--- Manage Showtimes (Add) ---")

        movies = self.movie_service.get_all_movies()
        if not movies:
            print("No movies available. Add a movie first.")
            return

        print("\nAvailable Movies:")
        MovieView.display_movies_table(movies)

        movie_id = Helpers.prompt_int("Enter Movie ID: ", min_val=1)
        if movie_id is None:
            return

        theater_id = Helpers.prompt_int("Enter Theater ID to see screens: ", min_val=1)
        if theater_id is None:
            return

        screens = self.theater_service.get_screens(theater_id)
        if not screens:
            print(f"[Error] No screens found for Theater ID {theater_id}.")
            return

        print(f"\nScreens in Theater {theater_id}:")
        for s in screens:
            print(f"ID: {s.screen_id} | Name: {s.screen_name} | Capacity: {s.capacity}")

        screen_id = Helpers.prompt_int("Enter Screen ID: ", min_val=1)
        if screen_id is None:
            return

        start_time = Helpers.prompt_datetime(
            "Start Time (YYYY-MM-DD HH:MM, e.g., 2026-08-15 18:30): "
        )
        if not start_time:
            return

        price = Helpers.prompt_float(
            "Ticket Price in USD (e.g., 12.50): ", min_val=0.01
        )
        if price is None:
            return

        try:
            self.showtime_service.add_showtime(
                movie_id, screen_id, start_time, price, admin_id
            )
            print("[Success] Showtime scheduled successfully.")
        except MovieTicketSystemError as e:
            print(f"[Error] {str(e)}")

    def view_movie_details_and_showtimes(self):
        print("\n--- View Movie Showtimes ---")
        movie_id = Helpers.prompt_int("Enter Movie ID: ", min_val=1)
        if movie_id is None:
            return

        movie = self.movie_service.get_movie(movie_id)
        if not movie:
            print("[Error] Movie not found.")
            return

        print("\n" + "=" * 40)
        print(f"🎬 {movie.title.upper()} ({movie.release_date})")
        print(f"⭐ Rating: {movie.rating} | ⏱ Duration: {movie.duration} mins")
        print(f"🎭 Genre: {movie.genre} | 🗣 Language: {movie.language}")
        print(f"📝 {movie.description}")
        print("=" * 40)

        showtimes = self.showtime_service.get_movie_showtimes(movie_id)
        if not showtimes:
            print("\nNo upcoming showtimes available for this movie.")
            return

        headers = [
            "Showtime ID",
            "Theater Name",
            "Screen",
            "Start Time",
            "Price",
            "Available Seats",
        ]
        rows = [
            [
                s["showtime_id"],
                s["theater_name"],
                s["screen_name"],
                s["start_time"],
                f"${s['price']:.2f}",
                s["available_seats"],
            ]
            for s in showtimes
        ]

        print("\nUpcoming Showtimes:")
        Helpers.print_table(headers, rows)

    def view_showtimes_by_theater(self):
        print("\n--- View Showtimes by Theater ---")
        theater_id = Helpers.prompt_int("Enter Theater ID: ", min_val=1)
        if theater_id is None:
            return

        date = Helpers.prompt_date("Enter Date (YYYY-MM-DD, e.g., 2026-08-15): ")
        if not date:
            return

        try:
            showtimes = self.showtime_service.get_theater_showtimes(theater_id, date)
            if not showtimes:
                print("No showtimes found for this location and date.")
                return

            headers = ["Movie Title", "Start Time", "Screen", "Price"]
            rows = [
                [s["title"], s["start_time"], s["screen_name"], f"${s['price']:.2f}"]
                for s in showtimes
            ]
            Helpers.print_table(headers, rows)

        except MovieTicketSystemError as e:
            print(f"[Error] {str(e)}")
