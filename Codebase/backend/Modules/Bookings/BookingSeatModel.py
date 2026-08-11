class BookingSeat:
    def __init__(
        self, booking_seat_id, booking_id, seat_number, price, created_at=None
    ):
        self.booking_seat_id = booking_seat_id
        self.booking_id = booking_id
        self.seat_number = seat_number
        self.price = price
        self.created_at = created_at
