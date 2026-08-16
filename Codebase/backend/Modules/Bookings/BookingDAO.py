from Db_utils import DatabaseConnectionManager
from Modules.Bookings.BookingModel import Booking
from Modules.Bookings.BookingSeatModel import BookingSeat

from Modules.Common.Enums import BookingStatus, PaymentStatus

class BookingDAO:
    def __init__(self):
        self.db = DatabaseConnectionManager()

    def get_booked_seats(self, showtime_id):
        query = """
            SELECT bs.seat_number
            FROM booking_seats bs
            JOIN bookings b ON bs.booking_id = b.booking_id
            WHERE b.showtime_id = ? AND b.status = 'CONFIRMED'
        """
        rows = self.db.fetchall(query, (showtime_id,))
        return [row['seat_number'] for row in rows]

    def get_by_id(self, booking_id):
        query = "SELECT * FROM bookings WHERE booking_id = ?"
        row = self.db.fetchone(query, (booking_id,))
        return self._map_booking(row) if row else None

    def get_seats_for_booking(self, booking_id):
        query = """
            SELECT seat_number, price
            FROM booking_seats
            WHERE booking_id = ?
            ORDER BY seat_number
        """
        return self.db.fetchall(query, (booking_id,))

    def get_active_bookings(self, user_id):
        """Confirmed bookings for a user, newest show first - used by the cancel screen."""
        query = """
            SELECT b.booking_id, m.title, s.start_time, t.name AS theater_name,
                   sc.screen_name, b.total_amount,
                   GROUP_CONCAT(bs.seat_number, ', ') AS seats
            FROM bookings b
            JOIN showtimes s ON b.showtime_id = s.showtime_id
            JOIN movies m ON s.movie_id = m.movie_id
            JOIN screens sc ON s.screen_id = sc.screen_id
            JOIN theaters t ON sc.theater_id = t.theater_id
            JOIN booking_seats bs ON b.booking_id = bs.booking_id
            WHERE b.user_id = ? AND b.status = 'CONFIRMED'
            GROUP BY b.booking_id
            ORDER BY s.start_time ASC
        """
        return self.db.fetchall(query, (user_id,))

    def get_customer_bookings(self, user_id, filter_type):
        query = """
            SELECT b.booking_id, m.title, s.start_time, b.total_amount, b.status,
                   t.name AS theater_name, t.city, sc.screen_name,
                   GROUP_CONCAT(bs.seat_number, ', ') as seats
            FROM bookings b
            JOIN showtimes s ON b.showtime_id = s.showtime_id
            JOIN movies m ON s.movie_id = m.movie_id
            JOIN screens sc ON s.screen_id = sc.screen_id
            JOIN theaters t ON sc.theater_id = t.theater_id
            JOIN booking_seats bs ON b.booking_id = bs.booking_id
            WHERE b.user_id = ?
        """
        params = [user_id]
        if filter_type == '1': # Upcoming
            query += " AND s.start_time > datetime('now', 'localtime')"
        elif filter_type == '2': # Past
            query += " AND s.start_time <= datetime('now', 'localtime')"

        query += " GROUP BY b.booking_id ORDER BY s.start_time DESC"

        return self.db.fetchall(query, tuple(params))

    def get_all_bookings(self):
        query = """
            SELECT b.booking_id, u.username, m.title, t.name as theater_name,
                   sc.screen_name, s.start_time, b.total_amount, b.status,
                   GROUP_CONCAT(bs.seat_number, ', ') as seats
            FROM bookings b
            JOIN users u ON b.user_id = u.user_id
            JOIN showtimes s ON b.showtime_id = s.showtime_id
            JOIN movies m ON s.movie_id = m.movie_id
            JOIN screens sc ON s.screen_id = sc.screen_id
            JOIN theaters t ON sc.theater_id = t.theater_id
            JOIN booking_seats bs ON b.booking_id = bs.booking_id
            GROUP BY b.booking_id
            ORDER BY b.booking_date DESC
        """
        return self.db.fetchall(query)

    def _map_booking(self, row):
        return Booking(
            booking_id=row['booking_id'],
            user_id=row['user_id'],
            showtime_id=row['showtime_id'],
            total_amount=row['total_amount'],
            status=BookingStatus(row['status']),
            payment_status=PaymentStatus(row['payment_status']),
            booking_date=row['booking_date'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
