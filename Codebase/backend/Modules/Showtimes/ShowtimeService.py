from datetime import datetime, timedelta

from Modules.Showtimes.ShowtimeDAO import ShowtimeDAO
from Modules.Showtimes.ShowtimeModel import Showtime
from Modules.Movies.MovieDAO import MovieDAO
from Modules.Theaters.TheaterDAO import TheaterDAO
from Modules.Audit.AuditService import AuditService
from Modules.Notifications.NotificationService import (
    NotificationService,
    ConsoleCustomerObserver,
)
from Modules.Common.Exceptions import (
    InvalidInputError,
    EntityNotFoundError,
    ShowtimeOverlapError,
)
from Modules.Common.Enums import AuditAction
from Modules.Common.Helpers import Helpers


class ShowtimeService:
    def __init__(self):
        self.showtime_dao = ShowtimeDAO()
        self.movie_dao = MovieDAO()
        self.theater_dao = TheaterDAO()
        self.audit_service = AuditService()
        self.notification_service = NotificationService()
        self.notification_service.attach(ConsoleCustomerObserver())

    def add_showtime(self, movie_id, screen_id, start_time_str, price, admin_id):
        if not Helpers.is_valid_datetime(start_time_str):
            raise InvalidInputError("Invalid start time format. Use YYYY-MM-DD HH:MM.")

        if price <= 0:
            raise InvalidInputError("Price must be greater than 0.")

        movie = self.movie_dao.get_by_id(movie_id)
        if not movie:
            raise EntityNotFoundError(f"Movie with ID {movie_id} not found.")

        # In a real app we'd need a screenDAO to fetch capacity. The TheaterDAO has `get_screens_by_theater`
        # Let's fetch the capacity from the DB directly or via DAO
        query = "SELECT capacity FROM screens WHERE screen_id = ?"
        row = self.showtime_dao.db.fetchone(query, (screen_id,))
        if not row:
            raise EntityNotFoundError(f"Screen with ID {screen_id} not found.")

        capacity = row["capacity"]

        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")

        # Every listing query filters on start_time > now, so a showtime scheduled in
        # the past would be invisible in the UI while still occupying its screen slot.
        if start_time <= datetime.now():
            raise InvalidInputError("Start time must be in the future.")

        # Add movie duration + some buffer (e.g., 30 mins for cleaning)
        end_time = start_time + timedelta(minutes=movie.duration + 30)
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M")

        # Check overlaps
        if self.showtime_dao.check_overlap(screen_id, start_time_str, end_time_str):
            raise ShowtimeOverlapError(
                "This showtime overlaps with an existing schedule on this screen."
            )

        showtime = Showtime(
            showtime_id=None,
            movie_id=movie_id,
            screen_id=screen_id,
            start_time=start_time_str,
            end_time=end_time_str,
            price=price,
            available_seats=capacity,
            created_by=admin_id,
        )

        showtime_id = self.showtime_dao.insert(showtime)
        showtime.showtime_id = showtime_id

        self.audit_service.log_action(
            "showtimes", showtime_id, AuditAction.INSERT, admin_id
        )

        # Notify
        self.notification_service._message = (
            f"[NOTIFICATION] New showtimes available for '{movie.title}'!"
        )
        self.notification_service.notify()

        return showtime

    def get_movie_showtimes(self, movie_id):
        return self.showtime_dao.get_available_showtimes_by_movie(movie_id)

    def get_showtime_details(self, showtime_id):
        return self.showtime_dao.get_showtime_details(showtime_id)

    def get_all_upcoming_showtimes(self):
        return self.showtime_dao.get_all_upcoming_showtimes()

    def get_upcoming_showtimes_grouped_by_movie(self):
        """All movies that have upcoming shows, each with its list of showtimes."""
        grouped = {}
        for row in self.showtime_dao.get_all_upcoming_showtimes():
            movie = grouped.setdefault(
                row["movie_id"],
                {
                    "movie_id": row["movie_id"],
                    "title": row["title"],
                    "genre": row["genre"],
                    "language": row["language"],
                    "duration": row["duration"],
                    "showtimes": [],
                },
            )
            movie["showtimes"].append(row)
        return list(grouped.values())

    def get_theater_showtimes(self, theater_id, date=None):
        if date and not Helpers.is_valid_date(date):
            raise InvalidInputError("Invalid date format. Use YYYY-MM-DD.")
        return self.showtime_dao.get_showtimes_by_theater(theater_id, date)

    def get_theater_show_dates(self, theater_id):
        return self.showtime_dao.get_showtime_dates_by_theater(theater_id)

    def get_theater(self, theater_id):
        return self.theater_dao.get_theater_by_id(theater_id)

    def get_movies_with_upcoming_shows(self):
        return self.showtime_dao.get_movies_with_upcoming_shows()

    def get_theaters_for_movie(self, movie_id):
        return self.showtime_dao.get_theaters_for_movie(movie_id)

    def get_movie_show_dates_at_theater(self, movie_id, theater_id):
        return self.showtime_dao.get_show_dates_for_movie_at_theater(
            movie_id, theater_id
        )

    def get_movie_showtimes_at_theater(self, movie_id, theater_id, date=None):
        if date and not Helpers.is_valid_date(date):
            raise InvalidInputError("Invalid date format. Use YYYY-MM-DD.")
        return self.showtime_dao.get_showtimes_for_movie_at_theater(
            movie_id, theater_id, date
        )

    def get_upcoming_show_dates(self):
        return self.showtime_dao.get_upcoming_show_dates()
