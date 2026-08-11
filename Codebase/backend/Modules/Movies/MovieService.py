from Modules.Movies.MovieDAO import MovieDAO
from Modules.Movies.MovieModel import Movie
from Modules.Movies.Strategies import MovieSearchStrategy
from Modules.Audit.AuditService import AuditService
from Modules.Notifications.NotificationService import (
    NotificationService,
    ConsoleCustomerObserver,
)
from Modules.Common.Exceptions import (
    InvalidInputError,
    EntityNotFoundError,
    ActiveBookingsExistError,
)
from Modules.Common.Enums import AuditAction
from Db_utils import DatabaseConnectionManager


class MovieService:
    def __init__(self):
        self.movie_dao = MovieDAO()
        self.audit_service = AuditService()
        self.notification_service = NotificationService()
        self.notification_service.attach(ConsoleCustomerObserver())
        self.db = DatabaseConnectionManager()

    def add_movie(self, movie):
        if not movie.title or not movie.duration or not movie.release_date:
            raise InvalidInputError("Title, duration, and release date are required.")

        if movie.duration <= 0:
            raise InvalidInputError("Duration must be a positive integer.")

        movie_id = self.movie_dao.insert(movie)
        movie.movie_id = movie_id

        # Log insertion
        self.audit_service.log_action(
            "movies", movie_id, AuditAction.INSERT, movie.created_by
        )

        # Notify Observers
        self.notification_service.notify_customers_of_new_movie(movie.title)

        return movie

    def update_movie(self, movie, admin_id):
        existing = self.movie_dao.get_by_id(movie.movie_id)
        if not existing:
            raise EntityNotFoundError(f"Movie with ID {movie.movie_id} not found.")

        self.movie_dao.update(movie)
        self.audit_service.log_action(
            "movies", movie.movie_id, AuditAction.UPDATE, admin_id
        )
        return movie

    def delete_movie(self, movie_id, admin_id):
        existing = self.movie_dao.get_by_id(movie_id)
        if not existing:
            raise EntityNotFoundError(f"Movie with ID {movie_id} not found.")

        # Check for active bookings
        query = """
            SELECT COUNT(*) as count 
            FROM bookings b
            JOIN showtimes s ON b.showtime_id = s.showtime_id
            WHERE s.movie_id = ? AND b.status = 'CONFIRMED'
        """
        row = self.db.fetchone(query, (movie_id,))
        if row and row["count"] > 0:
            raise ActiveBookingsExistError(
                "Cannot delete movie. Active bookings exist."
            )

        self.movie_dao.delete(movie_id)
        self.audit_service.log_action("movies", movie_id, AuditAction.DELETE, admin_id)

    def search_movies(self, strategy, query):
        return strategy.search(self.movie_dao, query)

    def get_all_movies(self):
        return self.movie_dao.get_all()

    def get_movie(self, movie_id):
        return self.movie_dao.get_by_id(movie_id)
