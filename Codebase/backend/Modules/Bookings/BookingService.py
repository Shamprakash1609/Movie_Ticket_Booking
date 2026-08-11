from Modules.Bookings.BookingDAO import BookingDAO
from Modules.Bookings.BookingBuilder import BookingBuilder
from Modules.Bookings.BookingModel import Booking
from Modules.Bookings.BookingSeatModel import BookingSeat
from Modules.Showtimes.ShowtimeDAO import ShowtimeDAO
from Modules.Audit.AuditService import AuditService
from Modules.Bookings.PricingStrategy import ShowtimePricingStrategy
from Modules.Common.Exceptions import (
    SeatAlreadyBookedError,
    EntityNotFoundError,
    CancellationError,
    InvalidInputError,
)
from Modules.Common.Enums import BookingStatus, PaymentStatus, AuditAction
from Db_utils import DatabaseConnectionManager


class BookingService:
    def __init__(self):
        self.booking_dao = BookingDAO()
        self.showtime_dao = ShowtimeDAO()
        self.audit_service = AuditService()
        self.db = DatabaseConnectionManager()

    def get_booked_seats(self, showtime_id):
        return self.booking_dao.get_booked_seats(showtime_id)

    def generate_seat_matrix(self, showtime_id):
        booked = self.get_booked_seats(showtime_id)
        # Simplified assumption: A-J rows, 1-10 cols (100 capacity)
        # In a real app, this should depend on the Screen capacity.
        # We will dynamically generate it based on capacity.
        showtime = self.showtime_dao.get_by_id(showtime_id)
        if not showtime:
            raise EntityNotFoundError("Showtime not found.")

        capacity = showtime.available_seats + len(booked)  # Total capacity

        all_seats = []
        rows = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
        cols = max(1, capacity // len(rows))

        for r in rows:
            for c in range(1, cols + 1):
                if len(all_seats) < capacity:
                    all_seats.append(f"{r}{c}")

        return all_seats, booked

    def book_tickets(self, user_id, showtime_id, selected_seats, strategy):
        showtime = self.showtime_dao.get_by_id(showtime_id)
        if not showtime:
            raise EntityNotFoundError("Showtime not found.")

        booked_seats = self.get_booked_seats(showtime_id)

        builder = BookingBuilder().set_user(user_id).set_showtime(showtime_id)

        for seat in selected_seats:
            if seat in booked_seats:
                raise SeatAlreadyBookedError(f"Seat {seat} is already booked.")

            price = strategy.calculate_price(showtime.price, seat)
            builder.add_seat(seat, price)

        booking = builder.build_booking()
        seats_to_book = builder.build_seats()

        try:
            # Transactional DB logic
            self.db.execute("BEGIN TRANSACTION")

            # 1. Insert into bookings
            cursor = self.db.execute(
                "INSERT INTO bookings (user_id, showtime_id, total_amount, status, payment_status) VALUES (?, ?, ?, ?, ?)",
                (
                    booking.user_id,
                    booking.showtime_id,
                    booking.total_amount,
                    booking.status.value,
                    booking.payment_status.value,
                ),
            )
            booking_id = cursor.lastrowid
            booking.booking_id = booking_id

            # 2. Insert into booking_seats
            seat_data = [
                (booking_id, seat.seat_number, seat.price) for seat in seats_to_book
            ]
            self.db.executemany(
                "INSERT INTO booking_seats (booking_id, seat_number, price) VALUES (?, ?, ?)",
                seat_data,
            )

            # 3. Decrement available seats
            self.db.execute(
                "UPDATE showtimes SET available_seats = available_seats - ? WHERE showtime_id = ?",
                (len(selected_seats), showtime_id),
            )

            self.db.commit()

            self.audit_service.log_action(
                "bookings", booking_id, AuditAction.INSERT, user_id
            )

            # Update payment status to COMPLETED (Simulated)
            self.db.execute(
                "UPDATE bookings SET payment_status = ? WHERE booking_id = ?",
                (PaymentStatus.COMPLETED.value, booking_id),
            )
            self.db.commit()

            return booking

        except Exception as e:
            self.db.rollback()
            raise e

    def get_customer_bookings(self, user_id, filter_type):
        return self.booking_dao.get_customer_bookings(user_id, filter_type)

    def get_all_bookings(self):
        return self.booking_dao.get_all_bookings()

    def cancel_booking(self, booking_id, user_id):
        booking = self.booking_dao.get_by_id(booking_id)
        if not booking:
            raise EntityNotFoundError("Booking not found.")

        if booking.user_id != user_id:
            raise CancellationError("You can only cancel your own bookings.")

        if booking.status == BookingStatus.CANCELLED:
            raise CancellationError("Booking is already cancelled.")

        showtime = self.showtime_dao.get_by_id(booking.showtime_id)

        # In a real app we'd compare showtime.start_time with current time properly
        # Assuming we just cancel if the showtime is still active (not deleted)
        if not showtime:
            raise CancellationError("Showtime no longer exists.")

        try:
            self.db.execute("BEGIN TRANSACTION")

            # 1. Update booking status
            self.db.execute(
                "UPDATE bookings SET status = ?, payment_status = ? WHERE booking_id = ?",
                (
                    BookingStatus.CANCELLED.value,
                    PaymentStatus.REFUNDED.value,
                    booking_id,
                ),
            )

            # 2. Get number of seats released
            cursor = self.db.execute(
                "SELECT COUNT(*) as cnt FROM booking_seats WHERE booking_id = ?",
                (booking_id,),
            )
            num_seats = cursor.fetchone()["cnt"]

            # 3. Restore seats
            self.db.execute(
                "UPDATE showtimes SET available_seats = available_seats + ? WHERE showtime_id = ?",
                (num_seats, booking.showtime_id),
            )

            self.db.commit()
            self.audit_service.log_action(
                "bookings", booking_id, AuditAction.UPDATE, user_id
            )

        except Exception as e:
            self.db.rollback()
            raise e
