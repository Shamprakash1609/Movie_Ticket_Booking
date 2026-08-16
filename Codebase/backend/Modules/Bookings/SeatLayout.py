import math


class SeatLayout:
    """Seating grid for a screen, derived from the capacity the admin configured.

    Rows are labelled A, B, C ... Z, AA, AB ... and every row is full except
    (possibly) the last one, so the number of seats always matches the screen
    capacity exactly.
    """

    MIN_COLS = 6
    MAX_COLS = 20

    def __init__(self, capacity):
        self.capacity = capacity
        self.cols = self._choose_cols(capacity)
        self.rows = []

        seats_left = capacity
        row_index = 0
        while seats_left > 0:
            label = self.row_label(row_index)
            count = min(self.cols, seats_left)
            self.rows.append((label, [f"{label}{c}" for c in range(1, count + 1)]))
            seats_left -= count
            row_index += 1

        self.all_seats = [seat for _, seats in self.rows for seat in seats]

    @staticmethod
    def row_of(seat_number):
        """'J13' -> 'J'."""
        return "".join(c for c in seat_number if c.isalpha()).upper()

    @staticmethod
    def sort_key(seat_number):
        """Natural seat order: J5 before J10, and row A before row B."""
        row = "".join(c for c in seat_number if c.isalpha())
        digits = "".join(c for c in seat_number if c.isdigit())
        return (len(row), row, int(digits) if digits else 0)

    @staticmethod
    def row_label(index):
        """0 -> A, 25 -> Z, 26 -> AA ..."""
        label = ""
        while True:
            label = chr(ord("A") + index % 26) + label
            index = index // 26 - 1
            if index < 0:
                break
        return label

    @classmethod
    def _choose_cols(cls, capacity):
        """Pick a seats-per-row that looks like a real auditorium.

        Prefers an exact divisor of the capacity near the ideal width so all
        rows come out even; falls back to the ideal width with a shorter last row.
        """
        if capacity <= cls.MIN_COLS:
            return max(1, capacity)

        ideal = min(cls.MAX_COLS, max(cls.MIN_COLS, math.ceil(math.sqrt(capacity * 1.8))))

        for delta in range(0, 5):
            for candidate in (ideal - delta, ideal + delta):
                if cls.MIN_COLS <= candidate <= cls.MAX_COLS and capacity % candidate == 0:
                    return candidate

        return ideal

    def has_seat(self, seat_number):
        return seat_number in self.all_seats
