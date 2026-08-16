from Modules.Bookings.BookingModel import Booking
from Modules.Bookings.BookingSeatModel import BookingSeat
from Modules.Common.Enums import BookingStatus, PaymentStatus
from Modules.Common.Exceptions import InvalidInputError


class BookingBuilder:
    """Builder Pattern for assembling Booking objects."""

    def __init__(self):
        self._booking = Booking(
            booking_id=None, user_id=0, showtime_id=0, total_amount=0.0
        )
        self._seats = []

    def set_user(self, user_id):
        self._booking.user_id = user_id
        return self

    def set_showtime(self, showtime_id):
        self._booking.showtime_id = showtime_id
        return self

    def add_seat(self, seat_number, price):
        seat = BookingSeat(
            booking_seat_id=None,
            booking_id=0,  # Will be set after booking insertion
            seat_number=seat_number,
            price=price,
        )
        self._seats.append(seat)
        self._booking.total_amount += price
        return self

    def set_status(self, status):
        self._booking.status = status
        return self

    def set_payment_status(self, status):
        self._booking.payment_status = status
        return self

    def build_booking(self):
        # InvalidInputError (not ValueError) so the controllers' existing
        # "except MovieTicketSystemError" handlers catch these instead of crashing.
        if self._booking.user_id == 0 or self._booking.showtime_id == 0:
            raise InvalidInputError("Booking must have a user and showtime.")
        if not self._seats:
            raise InvalidInputError("Booking must have at least one seat.")
        return self._booking

    def build_seats(self):
        return self._seats
