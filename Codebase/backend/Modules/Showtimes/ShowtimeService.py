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

    def get_theater_showtimes(self, theater_id, date):
        if not Helpers.is_valid_date(date):
            raise InvalidInputError("Invalid date format. Use YYYY-MM-DD.")
        return self.showtime_dao.get_showtimes_by_theater(theater_id, date)
