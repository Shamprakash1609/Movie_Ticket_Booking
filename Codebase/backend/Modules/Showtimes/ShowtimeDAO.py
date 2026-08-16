from Db_utils import DatabaseConnectionManager
from Modules.Showtimes.ShowtimeModel import Showtime


class ShowtimeDAO:
    def __init__(self):
        self.db = DatabaseConnectionManager()

    def insert(self, showtime):
        query = """
            INSERT INTO showtimes (movie_id, screen_id, start_time, end_time, price, available_seats, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self.db.execute(
            query,
            (
                showtime.movie_id,
                showtime.screen_id,
                showtime.start_time,
                showtime.end_time,
                showtime.price,
                showtime.available_seats,
                showtime.created_by,
            ),
        )
        self.db.commit()
        return cursor.lastrowid

    def check_overlap(self, screen_id, start_time, end_time):
        """Returns True if there is an overlapping showtime on the given screen."""
        query = """
            SELECT COUNT(*) as count FROM showtimes
            WHERE screen_id = ?
            AND (
                (start_time < ? AND end_time > ?) OR
                (start_time >= ? AND start_time < ?)
            )
        """
        # Logic:
        # existing starts before new ends AND existing ends after new starts
        row = self.db.fetchone(
            query, (screen_id, end_time, start_time, start_time, end_time)
        )
        return row["count"] > 0 if row else False

    def get_by_id(self, showtime_id):
        query = "SELECT * FROM showtimes WHERE showtime_id = ?"
        row = self.db.fetchone(query, (showtime_id,))
        return self._map_to_object(row) if row else None

    def get_available_showtimes_by_movie(self, movie_id):
        # Joins with screens and theaters for richer data display
        query = """
            SELECT s.showtime_id, t.name as theater_name, sc.screen_name, s.start_time, s.price, s.available_seats
            FROM showtimes s
            JOIN screens sc ON s.screen_id = sc.screen_id
            JOIN theaters t ON sc.theater_id = t.theater_id
            WHERE s.movie_id = ? AND s.start_time > datetime('now', 'localtime')
            ORDER BY s.start_time ASC
        """
        return self.db.fetchall(query, (movie_id,))

    def get_showtime_details(self, showtime_id):
        """Full context for a showtime: movie, screen (with its configured capacity) and theater."""
        query = """
            SELECT s.showtime_id, s.start_time, s.end_time, s.price, s.available_seats,
                   m.movie_id, m.title, m.duration, m.language,
                   sc.screen_id, sc.screen_name, sc.capacity AS screen_capacity,
                   t.theater_id, t.name AS theater_name, t.location, t.city
            FROM showtimes s
            JOIN movies m ON s.movie_id = m.movie_id
            JOIN screens sc ON s.screen_id = sc.screen_id
            JOIN theaters t ON sc.theater_id = t.theater_id
            WHERE s.showtime_id = ?
        """
        return self.db.fetchone(query, (showtime_id,))

    def get_all_upcoming_showtimes(self):
        """Every upcoming showtime across all movies, ordered for a browsable listing."""
        query = """
            SELECT m.movie_id, m.title, m.genre, m.language, m.duration,
                   s.showtime_id, t.name AS theater_name, sc.screen_name,
                   s.start_time, s.price, s.available_seats
            FROM showtimes s
            JOIN movies m ON s.movie_id = m.movie_id
            JOIN screens sc ON s.screen_id = sc.screen_id
            JOIN theaters t ON sc.theater_id = t.theater_id
            WHERE s.start_time > datetime('now', 'localtime')
            ORDER BY m.title ASC, s.start_time ASC
        """
        return self.db.fetchall(query)

    def get_showtimes_by_theater(self, theater_id, date=None):
        """Showtimes at a theater; pass date=None for every upcoming date."""
        query = """
            SELECT s.showtime_id, m.title, s.start_time, sc.screen_name, s.price,
                   s.available_seats
            FROM showtimes s
            JOIN movies m ON s.movie_id = m.movie_id
            JOIN screens sc ON s.screen_id = sc.screen_id
            WHERE sc.theater_id = ? AND s.start_time > datetime('now', 'localtime')
        """
        params = [theater_id]

        if date:
            query += " AND DATE(s.start_time) = ?"
            params.append(date)

        query += " ORDER BY s.start_time ASC, m.title ASC"
        return self.db.fetchall(query, tuple(params))

    def get_movies_with_upcoming_shows(self):
        """One row per movie that has upcoming shows, with a count of where it plays."""
        query = """
            SELECT m.movie_id, m.title, m.genre, m.language, m.duration, m.rating,
                   COUNT(DISTINCT t.theater_id) AS theater_count,
                   COUNT(s.showtime_id) AS show_count,
                   MIN(s.start_time) AS next_show
            FROM showtimes s
            JOIN movies m ON s.movie_id = m.movie_id
            JOIN screens sc ON s.screen_id = sc.screen_id
            JOIN theaters t ON sc.theater_id = t.theater_id
            WHERE s.start_time > datetime('now', 'localtime')
            GROUP BY m.movie_id
            ORDER BY m.title ASC
        """
        return self.db.fetchall(query)

    def get_theaters_for_movie(self, movie_id):
        """Theaters that have upcoming shows of this movie."""
        query = """
            SELECT t.theater_id, t.name AS theater_name, t.location, t.city,
                   COUNT(DISTINCT sc.screen_id) AS screen_count,
                   COUNT(s.showtime_id) AS show_count,
                   MIN(s.start_time) AS next_show
            FROM showtimes s
            JOIN screens sc ON s.screen_id = sc.screen_id
            JOIN theaters t ON sc.theater_id = t.theater_id
            WHERE s.movie_id = ? AND s.start_time > datetime('now', 'localtime')
            GROUP BY t.theater_id
            ORDER BY t.city ASC, t.name ASC
        """
        return self.db.fetchall(query, (movie_id,))

    def get_show_dates_for_movie_at_theater(self, movie_id, theater_id):
        """Upcoming dates on which this movie plays at this theater."""
        query = """
            SELECT DATE(s.start_time) AS show_date, COUNT(*) AS show_count
            FROM showtimes s
            JOIN screens sc ON s.screen_id = sc.screen_id
            WHERE s.movie_id = ? AND sc.theater_id = ?
              AND s.start_time > datetime('now', 'localtime')
            GROUP BY show_date
            ORDER BY show_date ASC
        """
        return self.db.fetchall(query, (movie_id, theater_id))

    def get_showtimes_for_movie_at_theater(self, movie_id, theater_id, date=None):
        """Shows of one movie at one theater, grouped screen by screen."""
        query = """
            SELECT s.showtime_id, s.start_time, s.price, s.available_seats,
                   sc.screen_id, sc.screen_name, sc.capacity AS screen_capacity
            FROM showtimes s
            JOIN screens sc ON s.screen_id = sc.screen_id
            WHERE s.movie_id = ? AND sc.theater_id = ?
              AND s.start_time > datetime('now', 'localtime')
        """
        params = [movie_id, theater_id]

        if date:
            query += " AND DATE(s.start_time) = ?"
            params.append(date)

        query += " ORDER BY sc.screen_name ASC, s.start_time ASC"
        return self.db.fetchall(query, tuple(params))

    def get_upcoming_show_dates(self):
        """Every upcoming date that has at least one show, system wide."""
        query = """
            SELECT DATE(s.start_time) AS show_date,
                   COUNT(*) AS show_count,
                   COUNT(DISTINCT s.movie_id) AS movie_count
            FROM showtimes s
            WHERE s.start_time > datetime('now', 'localtime')
            GROUP BY show_date
            ORDER BY show_date ASC
        """
        return self.db.fetchall(query)

    def get_showtime_dates_by_theater(self, theater_id):
        """Upcoming dates that actually have shows at this theater."""
        query = """
            SELECT DATE(s.start_time) AS show_date, COUNT(*) AS show_count
            FROM showtimes s
            JOIN screens sc ON s.screen_id = sc.screen_id
            WHERE sc.theater_id = ? AND s.start_time > datetime('now', 'localtime')
            GROUP BY show_date
            ORDER BY show_date ASC
        """
        return self.db.fetchall(query, (theater_id,))

    def _map_to_object(self, row):
        return Showtime(
            showtime_id=row["showtime_id"],
            movie_id=row["movie_id"],
            screen_id=row["screen_id"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            price=row["price"],
            available_seats=row["available_seats"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
