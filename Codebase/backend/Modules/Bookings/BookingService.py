from datetime import datetime

from Modules.Bookings.BookingDAO import BookingDAO
from Modules.Bookings.BookingBuilder import BookingBuilder
from Modules.Bookings.BookingModel import Booking
from Modules.Bookings.BookingSeatModel import BookingSeat
from Modules.Bookings.SeatLayout import SeatLayout
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
        """Builds the seating grid from the screen capacity the admin configured."""
        details = self.showtime_dao.get_showtime_details(showtime_id)
        if not details:
            raise EntityNotFoundError("Showtime not found.")

        booked = self.get_booked_seats(showtime_id)
        layout = SeatLayout(details["screen_capacity"])

        return layout, booked, details

    def book_tickets(self, user_id, showtime_id, selected_seats, strategy):
        showtime = self.showtime_dao.get_by_id(showtime_id)
        if not showtime:
            raise EntityNotFoundError("Showtime not found.")

        layout, booked_seats, _ = self.generate_seat_matrix(showtime_id)

        if len(set(selected_seats)) != len(selected_seats):
            raise InvalidInputError("The same seat was selected more than once.")

        builder = BookingBuilder().set_user(user_id).set_showtime(showtime_id)

        for seat in selected_seats:
            if not layout.has_seat(seat):
                raise InvalidInputError(
                    f"Seat {seat} does not exist on this screen. "
                    f"Valid seats run from {layout.all_seats[0]} to {layout.all_seats[-1]}."
                )

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

    def get_booking_seats(self, booking_id):
        seats = self.booking_dao.get_seats_for_booking(booking_id)
        return sorted(seats, key=lambda s: SeatLayout.sort_key(s["seat_number"]))

    def get_active_bookings(self, user_id):
        return self.booking_dao.get_active_bookings(user_id)

    def _load_cancellable_booking(self, booking_id, user_id):
        booking = self.booking_dao.get_by_id(booking_id)
        if not booking:
            raise EntityNotFoundError("Booking not found.")

        if booking.user_id != user_id:
            raise CancellationError("You can only cancel your own bookings.")

        if booking.status == BookingStatus.CANCELLED:
            raise CancellationError("Booking is already cancelled.")

        showtime = self.showtime_dao.get_by_id(booking.showtime_id)

        if not showtime:
            raise CancellationError("Showtime no longer exists.")

        # start_time is stored as 'YYYY-MM-DD HH:MM', which compares correctly as a
        # string against the same format. Refunding a show that already started is not
        # something the customer should be able to do.
        if showtime.start_time <= datetime.now().strftime("%Y-%m-%d %H:%M"):
            raise CancellationError(
                "This show has already started and can no longer be cancelled."
            )

        return booking

    def cancel_seats(self, booking_id, user_id, seat_numbers):
        """Releases individual seats from a booking and refunds only those seats.

        Cancelling every seat is the same as cancelling the whole booking.
        """
        booking = self._load_cancellable_booking(booking_id, user_id)

        if not seat_numbers:
            raise InvalidInputError("Select at least one seat to cancel.")

        if len(set(seat_numbers)) != len(seat_numbers):
            raise InvalidInputError("The same seat was listed more than once.")

        seat_prices = {
            s["seat_number"]: s["price"]
            for s in self.booking_dao.get_seats_for_booking(booking_id)
        }

        unknown = [s for s in seat_numbers if s not in seat_prices]
        if unknown:
            raise InvalidInputError(
                f"Seat(s) {', '.join(unknown)} are not part of booking #{booking_id}."
            )

        if len(seat_numbers) == len(seat_prices):
            return self.cancel_booking(booking_id, user_id)

        refund = sum(seat_prices[s] for s in seat_numbers)

        try:
            self.db.execute("BEGIN TRANSACTION")

            placeholders = ",".join("?" for _ in seat_numbers)
            self.db.execute(
                f"DELETE FROM booking_seats WHERE booking_id = ? AND seat_number IN ({placeholders})",
                (booking_id, *seat_numbers),
            )

            self.db.execute(
                "UPDATE bookings SET total_amount = total_amount - ?, updated_at = CURRENT_TIMESTAMP "
                "WHERE booking_id = ?",
                (refund, booking_id),
            )

            self.db.execute(
                "UPDATE showtimes SET available_seats = available_seats + ? WHERE showtime_id = ?",
                (len(seat_numbers), booking.showtime_id),
            )

            self.db.commit()
            self.audit_service.log_action(
                "booking_seats", booking_id, AuditAction.DELETE, user_id
            )

            return refund

        except Exception as e:
            self.db.rollback()
            raise e

    def cancel_booking(self, booking_id, user_id):
        booking = self._load_cancellable_booking(booking_id, user_id)

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

            return booking.total_amount

        except Exception as e:
            self.db.rollback()
            raise e
