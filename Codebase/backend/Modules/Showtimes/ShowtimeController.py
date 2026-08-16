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

        movie_id = Helpers.prompt_int("Enter Movie ID: ", min_val=1)
        if movie_id is None:
            return

        theaters = self.theater_service.get_all_theaters()
        if not theaters:
            print("No theaters available. Add a theater first.")
            return

        print("\nAvailable Theaters:")
        Helpers.print_table(
            ["ID", "Name", "Location", "City"],
            [[t.theater_id, t.name, t.location, t.city] for t in theaters],
        )

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
            "Ticket Price in INR (e.g., 250.00): ", min_val=0.01
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

    def _display_now_showing(self):
        """Lists every movie with its upcoming showtimes. Returns the valid movie IDs."""
        movies = self.movie_service.get_all_movies()
        if not movies:
            print("No movies available at the moment.")
            return None

        scheduled = {
            m["movie_id"]: m
            for m in self.showtime_service.get_upcoming_showtimes_grouped_by_movie()
        }

        if scheduled:
            print("\n🎟  NOW SHOWING")
            for movie in scheduled.values():
                print(
                    f"\n🎬 [Movie ID: {movie['movie_id']}] {movie['title'].upper()} "
                    f"— {movie['genre']} | {movie['language']} | {movie['duration']} mins"
                )
                headers = [
                    "Showtime ID",
                    "Theater",
                    "Screen",
                    "Start Time",
                    "Price",
                    "Seats Left",
                ]
                rows = [
                    [
                        s["showtime_id"],
                        s["theater_name"],
                        s["screen_name"],
                        s["start_time"],
                        f"₹{s['price']:.2f}",
                        s["available_seats"],
                    ]
                    for s in movie["showtimes"]
                ]
                Helpers.print_table(headers, rows)
        else:
            print("\nNo upcoming showtimes are scheduled right now.")

        unscheduled = [m for m in movies if m.movie_id not in scheduled]
        if unscheduled:
            print("\n📅 COMING SOON (no showtimes scheduled yet)")
            MovieView.display_movies_table(unscheduled)

        return {m.movie_id for m in movies}

    def view_movie_details_and_showtimes(self):
        print("\n--- View Movie Details & Available Showtimes ---")

        valid_ids = self._display_now_showing()
        if valid_ids is None:
            return

        print("(Type 'c' to go back)")
        while True:
            movie_id = Helpers.prompt_int(
                "\nEnter Movie ID to see full details: ", min_val=1
            )
            if movie_id is None:
                return
            if movie_id in valid_ids:
                break
            print(f"[Input Error] {movie_id} is not in the list above. Please try again.")

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
                f"₹{s['price']:.2f}",
                s["available_seats"],
            ]
            for s in showtimes
        ]

        print("\nUpcoming Showtimes:")
        Helpers.print_table(headers, rows)

    def view_showtimes_by_theater(self):
        print("\n--- View Showtimes by Theater ---")

        theaters = self.theater_service.get_all_theaters()
        if not theaters:
            print("No theaters available.")
            return

        print("\nAvailable Theaters:")
        Helpers.print_table(
            ["#", "Name", "Location", "City", "Total Seats"],
            [
                [i + 1, t.name, t.location, t.city, t.capacity]
                for i, t in enumerate(theaters)
            ],
        )

        choice = Helpers.prompt_list_choice("Select a theatre (#): ", len(theaters))
        if choice is None:
            return
        theater = theaters[choice]

        dates = self.showtime_service.get_theater_show_dates(theater.theater_id)
        if not dates:
            print(f"\nNo upcoming showtimes at {theater.name}, {theater.city}.")
            return

        print(f"\n📅 Dates with shows at {theater.name} — {theater.location}, {theater.city}:")
        rows = [
            [i + 1, d["show_date"], Helpers.day_name(d["show_date"]), d["show_count"]]
            for i, d in enumerate(dates)
        ]
        # "All dates" only earns a row when there is more than one date to merge.
        if len(dates) > 1:
            rows.append(
                [len(dates) + 1, "All dates", "-", sum(d["show_count"] for d in dates)]
            )
        Helpers.print_table(["#", "Date", "Day", "Shows"], rows)

        choice = Helpers.prompt_list_choice("Select a date (#): ", len(rows))
        if choice is None:
            return
        # The extra row past the last date is the "All dates" option.
        date = None if choice == len(dates) else dates[choice]["show_date"]

        try:
            showtimes = self.showtime_service.get_theater_showtimes(
                theater.theater_id, date
            )
            if not showtimes:
                print("No showtimes found for this theatre and date.")
                return

            when = date or "all upcoming dates"
            print(f"\n🎟  Shows at {theater.name}, {theater.city} — {when}")
            headers = [
                "Movie Title",
                "Screen",
                "Start Time",
                "Day",
                "Price",
                "Seats Left",
            ]
            rows = [
                [
                    s["title"],
                    s["screen_name"],
                    s["start_time"],
                    Helpers.day_name(s["start_time"]),
                    f"₹{s['price']:.2f}",
                    s["available_seats"],
                ]
                for s in showtimes
            ]
            Helpers.print_table(headers, rows)

        except MovieTicketSystemError as e:
            print(f"[Error] {str(e)}")
