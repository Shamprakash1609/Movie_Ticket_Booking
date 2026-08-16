from abc import ABC, abstractmethod


class ShowtimePricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, base_price, seat_number):
        pass


class BasePricingStrategy(ShowtimePricingStrategy):
    # The booking screen reads vip_rows/premium off whichever strategy it is given,
    # so every strategy must expose them or it cannot be substituted for another.
    vip_rows = ()
    premium = 0.0

    def calculate_price(self, base_price, seat_number):
        return base_price


class VIPRowPricingStrategy(ShowtimePricingStrategy):
    """Adds a premium for the VIP rows - the back rows of the auditorium.

    Screens no longer all have the same number of rows, so the caller passes the
    rows that are actually at the back (see BookingController). Rows E and F are
    the fallback for callers that don't know the layout.
    """

    DEFAULT_VIP_ROWS = ("E", "F")
    PREMIUM = 100.0  # a VIP seat costs this much more than a normal seat

    def __init__(self, vip_rows=None, premium=None):
        # `is None` rather than a truthiness test: an explicitly empty sequence means
        # "this screen has no VIP rows" and must not silently fall back to the default.
        self.vip_rows = (
            self.DEFAULT_VIP_ROWS
            if vip_rows is None
            else tuple(r.upper() for r in vip_rows)
        )
        self.premium = self.PREMIUM if premium is None else premium

    def calculate_price(self, base_price, seat_number):
        row = "".join(c for c in seat_number if c.isalpha()).upper()
        if row in self.vip_rows:
            return base_price + self.premium
        return base_price
