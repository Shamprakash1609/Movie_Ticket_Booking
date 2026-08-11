from Modules.Common.Enums import BookingStatus, PaymentStatus


class Booking:
    def __init__(
        self,
        booking_id,
        user_id,
        showtime_id,
        total_amount,
        status=BookingStatus.CONFIRMED,
        payment_status=PaymentStatus.PENDING,
        booking_date=None,
        created_at=None,
        updated_at=None,
    ):
        self.booking_id = booking_id
        self.user_id = user_id
        self.showtime_id = showtime_id
        self.total_amount = total_amount
        self.status = status
        self.payment_status = payment_status
        self.booking_date = booking_date
        self.created_at = created_at
        self.updated_at = updated_at
