class Showtime:
    def __init__(
        self,
        showtime_id,
        movie_id,
        screen_id,
        start_time,
        end_time,
        price,
        available_seats,
        created_by,
        created_at=None,
        updated_at=None,
    ):
        self.showtime_id = showtime_id
        self.movie_id = movie_id
        self.screen_id = screen_id
        self.start_time = start_time
        self.end_time = end_time
        self.price = price
        self.available_seats = available_seats
        self.created_by = created_by
        self.created_at = created_at
        self.updated_at = updated_at
