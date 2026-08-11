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

    def get_showtimes_by_theater(self, theater_id, date):
        query = """
            SELECT m.title, s.start_time, sc.screen_name, s.price
            FROM showtimes s
            JOIN movies m ON s.movie_id = m.movie_id
            JOIN screens sc ON s.screen_id = sc.screen_id
            WHERE sc.theater_id = ? AND s.start_time LIKE ?
            ORDER BY m.title, s.start_time ASC
        """
        return self.db.fetchall(query, (theater_id, f"{date}%"))

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
