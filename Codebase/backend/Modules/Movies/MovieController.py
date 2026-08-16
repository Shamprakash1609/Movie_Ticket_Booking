from Modules.Movies.MovieService import MovieService
from Modules.Movies.MovieModel import Movie
from Modules.Movies.MovieView import MovieView
from Modules.Movies.Strategies import (
    SearchByTitleStrategy,
    SearchByGenreStrategy,
    SearchByLanguageStrategy,
    SearchByShowDateStrategy,
    SearchByTheaterStrategy,
    SearchByReleaseDateStrategy,
    CustomFilterStrategy,
)
from Modules.Showtimes.ShowtimeService import ShowtimeService
from Modules.Theaters.TheaterService import TheaterService
from Modules.Common.Exceptions import MovieTicketSystemError
from Modules.Common.Helpers import Helpers


class MovieController:
    def __init__(self):
        self.movie_service = MovieService()
        self.showtime_service = ShowtimeService()
        self.theater_service = TheaterService()

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

    def _pick_show_date(self):
        """Lets the user pick from the dates that actually have shows scheduled."""
        dates = self.showtime_service.get_upcoming_show_dates()
        if not dates:
            print("No upcoming showtimes are scheduled right now.")
            return None

        print("\nDates with shows scheduled:")
        Helpers.print_table(
            ["#", "Date", "Day", "Movies", "Shows"],
            [
                [
                    i + 1,
                    d["show_date"],
                    Helpers.day_name(d["show_date"]),
                    d["movie_count"],
                    d["show_count"],
                ]
                for i, d in enumerate(dates)
            ],
        )
        choice = Helpers.prompt_list_choice("Select a date (#): ", len(dates))
        return None if choice is None else dates[choice]["show_date"]

    def _pick_theater(self):
        theaters = self.theater_service.get_all_theaters()
        if not theaters:
            print("No theatres available.")
            return None

        print("\nAvailable Theatres:")
        Helpers.print_table(
            ["#", "Name", "Location", "City"],
            [
                [i + 1, t.name, t.location, t.city]
                for i, t in enumerate(theaters)
            ],
        )
        choice = Helpers.prompt_list_choice("Select a theatre (#): ", len(theaters))
        return None if choice is None else theaters[choice]

    # The fields the admin can switch on in the custom filter. Nothing here is
    # mandatory - a field the admin never sets is simply left out of the query.
    CUSTOM_FILTERS = [
        {
            "key": "title",
            "label": "Movie title contains",
            "example": "leo",
            "hint": "Matches any part of the title. Case does not matter.",
            "type": "text",
        },
        {
            "key": "genre",
            "label": "Genre contains",
            "example": "Action",
            "hint": "Matches part of the genre, so 'Action' also finds 'Action Comedy'.",
            "type": "text",
        },
        {
            "key": "language",
            "label": "Language contains",
            "example": "Tamil",
            "hint": "Matches part of the language name.",
            "type": "text",
        },
        {
            "key": "released_from",
            "label": "Released on or after",
            "example": "2024-01-01",
            "hint": "Keeps movies released on this date or later.",
            "type": "date",
        },
        {
            "key": "released_to",
            "label": "Released on or before",
            "example": "2026-12-31",
            "hint": "Keeps movies released on this date or earlier.",
            "type": "date",
        },
        {
            "key": "min_rating",
            "label": "Rating at least",
            "example": "7.5",
            "hint": "Keeps movies rated this high or higher (0 to 10).",
            "type": "rating",
        },
        {
            "key": "max_duration",
            "label": "Runtime at most (mins)",
            "example": "150",
            "hint": "Keeps movies no longer than this many minutes.",
            "type": "minutes",
        },
        {
            "key": "show_date",
            "label": "Has a show on date",
            "example": "2026-08-15",
            "hint": "Keeps movies scheduled on that date. Past dates are allowed here.",
            "type": "show_date",
        },
        {
            "key": "theater_id",
            "label": "Playing at theatre",
            "example": "PVR INOX",
            "hint": "Pick a theatre from a list - no ID to remember.",
            "type": "theater",
        },
        {
            "key": "city",
            "label": "Theatre city contains",
            "example": "Chennai",
            "hint": "Keeps movies showing in theatres in that city.",
            "type": "text",
        },
    ]

    def _show_filter_builder(self, shown):
        """Prints the builder screen: every field, and whether it is set or skipped."""
        print("\n" + "=" * 78)
        print(" CUSTOM FILTER — build your search one field at a time")
        print("=" * 78)
        print(" Every field below is OPTIONAL.")
        print("   • A field you never touch stays SKIPPED and is left out of the search.")
        print("   • Fields you do set are combined with AND — a movie must match them all.")
        print("   • Nothing is searched until you press 'a'.")

        Helpers.print_table(
            ["#", "Filter", "Example", "Current value"],
            [
                [i + 1, f["label"], f["example"], shown.get(f["key"], "— skipped —")]
                for i, f in enumerate(self.CUSTOM_FILTERS)
            ],
        )

        active = [
            f"{f['label']} = {shown[f['key']]}"
            for f in self.CUSTOM_FILTERS
            if f["key"] in shown
        ]
        if active:
            print(f" Searching for: {' AND '.join(active)}")
        else:
            print(" Searching for: nothing yet — right now this would return every movie.")

        commands = [
            (f"1-{len(self.CUSTOM_FILTERS)}", "set or change that filter",
             "r", "remove one filter"),
            ("v", "preview how many movies match", "a", "apply and show results"),
            ("x", "skip everything / start over", "c", "cancel and go back"),
        ]
        print("\n Commands:")
        for key, action, alt_key, alt_action in commands:
            print(f"   {key:<6}{action:<32}{alt_key:<4}{alt_action}")

    @staticmethod
    def _parse_filter_value(field, raw):
        """Turns typed text into a filter value, or raises ValueError with advice."""
        kind = field["type"]

        if kind in ("date", "show_date"):
            if not Helpers.is_valid_date(raw):
                raise ValueError(
                    f"Dates must look like YYYY-MM-DD, e.g. {field['example']}."
                )
            return raw

        if kind == "rating":
            try:
                value = float(raw)
            except ValueError:
                raise ValueError("Enter a number between 0 and 10, e.g. 7.5.")
            if not 0 <= value <= 10:
                raise ValueError("A rating has to be between 0 and 10.")
            return value

        if kind == "minutes":
            try:
                value = int(raw)
            except ValueError:
                raise ValueError("Enter a whole number of minutes, e.g. 150.")
            if value <= 0:
                raise ValueError("Runtime must be greater than 0 minutes.")
            return value

        return raw

    def _set_filter(self, field, criteria, shown):
        """Asks for one filter's value. Blank input leaves that filter skipped."""
        print(f"\n--- {field['label']} ---")
        print(f"  {field['hint']}")
        print(f"  Example: {field['example']}")

        if field["key"] in criteria:
            print(f"  Currently set to: {shown[field['key']]}")

        if field["type"] == "theater":
            print("  (Choose 'c' at the theatre list to leave this filter alone.)")
            theater = self._pick_theater()
            if theater is None:
                print(f"[Unchanged] '{field['label']}' was not modified.")
                return
            criteria[field["key"]] = theater.theater_id
            shown[field["key"]] = f"{theater.name}, {theater.city}"
            print(f"[Set] {field['label']} = {shown[field['key']]}")
            return

        if field["type"] == "show_date":
            print("  Tip: type 'l' to pick from the dates that have shows scheduled.")

        print("  Press Enter on its own to SKIP this filter (or clear it if it is set).")

        while True:
            raw = input(f"  {field['label']}: ").strip()

            if not raw:
                existed = criteria.pop(field["key"], None) is not None
                shown.pop(field["key"], None)
                print(
                    f"[Cleared] '{field['label']}' is no longer part of the search."
                    if existed
                    else f"[Skipped] '{field['label']}' is not part of the search."
                )
                return

            if field["type"] == "show_date" and raw.lower() == "l":
                date = self._pick_show_date()
                if date is None:
                    print(f"[Unchanged] '{field['label']}' was not modified.")
                    return
                criteria[field["key"]] = date
                shown[field["key"]] = f"{date} ({Helpers.day_name(date)})"
                print(f"[Set] {field['label']} = {shown[field['key']]}")
                return

            try:
                value = self._parse_filter_value(field, raw)
            except ValueError as e:
                print(f"[Input Error] {e} Or press Enter to skip this filter.")
                continue

            criteria[field["key"]] = value
            shown[field["key"]] = (
                f"{value} ({Helpers.day_name(value)})"
                if field["type"] in ("date", "show_date")
                else str(value)
            )
            print(f"[Set] {field['label']} = {shown[field['key']]}")
            return

    def _remove_filter(self, criteria, shown):
        active = [f for f in self.CUSTOM_FILTERS if f["key"] in criteria]
        if not active:
            print("\nThere are no filters to remove — everything is already skipped.")
            return

        print("\nFilters currently in the search:")
        Helpers.print_table(
            ["#", "Filter", "Value"],
            [[i + 1, f["label"], shown[f["key"]]] for i, f in enumerate(active)],
        )
        choice = Helpers.prompt_list_choice("Remove which filter (#): ", len(active))
        if choice is None:
            return

        field = active[choice]
        criteria.pop(field["key"])
        shown.pop(field["key"])
        print(f"[Removed] '{field['label']}' is back to skipped.")

    def _custom_filter(self):
        """Guided multi-criteria filter builder.

        Returns the matching movies, or None if the admin backed out.
        """
        criteria = {}
        shown = {}  # key -> the human-readable value printed in the builder table

        while True:
            self._show_filter_builder(shown)
            command = input("\n Command: ").strip().lower()

            if command in ("c", "cancel", "q", "quit"):
                print("Custom filter cancelled — nothing was searched.")
                return None

            if command == "x":
                criteria.clear()
                shown.clear()
                print("[Cleared] All filters skipped. The search would return every movie.")
                continue

            if command == "r":
                self._remove_filter(criteria, shown)
                continue

            if command in ("v", "a"):
                if not criteria:
                    print("\nNo filters are set — this returns every movie in the system.")
                    if command == "a":
                        confirm = input("Continue anyway? [y/N]: ").strip().lower()
                        if confirm != "y":
                            continue

                movies = self.movie_service.search_movies(
                    CustomFilterStrategy(), criteria
                )

                if command == "a":
                    return movies

                print(f"\n[Preview] {len(movies)} movie(s) match right now.")
                if movies:
                    preview = ", ".join(m.title for m in movies[:8])
                    more = "" if len(movies) <= 8 else f", … +{len(movies) - 8} more"
                    print(f"          {preview}{more}")
                else:
                    print("          Try removing a filter with 'r' to widen the search.")
                continue

            if command.isdigit() and 1 <= int(command) <= len(self.CUSTOM_FILTERS):
                self._set_filter(
                    self.CUSTOM_FILTERS[int(command) - 1], criteria, shown
                )
                continue

            print(
                f"[Input Error] Enter 1-{len(self.CUSTOM_FILTERS)} to set a filter, "
                "or r / v / a / x / c."
            )

    def view_movies_admin(self):
        print("\n--- View/Search Movies ---")
        print("1. View All")
        print("2. Search by Title")
        print("3. Search by Genre")
        print("4. Search by Language")
        print("5. Filter by Release Date (range)")
        print("6. Filter by Show Date")
        print("7. Filter by Theatre")
        print("8. Custom Filter (guided — combine any of the above)")

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

        elif choice == "4":
            query = Helpers.prompt_non_empty("Enter Language (e.g., Tamil): ")
            if not query:
                return
            movies = self.movie_service.search_movies(SearchByLanguageStrategy(), query)

        elif choice == "5":
            print("(Press Enter to leave a side of the range open)")
            released_from = self._prompt_optional_date("Released on or after")
            released_to = self._prompt_optional_date("Released on or before")
            movies = self.movie_service.search_movies(
                SearchByReleaseDateStrategy(), (released_from, released_to)
            )

        elif choice == "6":
            date = self._pick_show_date()
            if not date:
                return
            movies = self.movie_service.search_movies(SearchByShowDateStrategy(), date)
            print(f"\nMovies with shows on {date} ({Helpers.day_name(date)}):")

        elif choice == "7":
            theater = self._pick_theater()
            if not theater:
                return
            movies = self.movie_service.search_movies(
                SearchByTheaterStrategy(), theater.theater_id
            )
            print(f"\nMovies currently running at {theater.name}, {theater.city}:")

        elif choice == "8":
            movies = self._custom_filter()
            if movies is None:  # backed out of the builder
                return

        else:
            print("[Error] Invalid choice.")
            return

        if not movies:
            print("No movies matched your search.")
            return

        print(f"\n{len(movies)} movie(s) found.")
        MovieView.display_movies_table(movies)

    @staticmethod
    def _prompt_optional_date(prompt_text):
        """A date field that may be left blank. Returns None when skipped."""
        while True:
            value = input(f"{prompt_text} (YYYY-MM-DD, Enter to skip): ").strip()
            if not value:
                return None
            if Helpers.is_valid_date(value):
                return value
            print("[Input Error] Use YYYY-MM-DD (e.g., 2026-08-15), or Enter to skip.")

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
        print("4. Filter by Date (movies playing on a given date)")

        choice = input("Choice: ").strip()
        movies = []

        if choice == "1":
            movies = self.movie_service.get_all_movies()
        elif choice == "2":
            lang = Helpers.prompt_non_empty("Enter Language: ")
            if not lang:
                return
            movies = self.movie_service.search_movies(SearchByLanguageStrategy(), lang)
        elif choice == "3":
            genre = Helpers.prompt_non_empty("Enter Genre: ")
            if not genre:
                return
            movies = self.movie_service.search_movies(SearchByGenreStrategy(), genre)
        elif choice == "4":
            date = self._pick_show_date()
            if not date:
                return
            movies = self.movie_service.search_movies(SearchByShowDateStrategy(), date)
            print(f"\n🎬 Playing on {date} ({Helpers.day_name(date)}):")
        else:
            print("[Error] Invalid choice.")
            return

        MovieView.display_movie_cards(movies)
