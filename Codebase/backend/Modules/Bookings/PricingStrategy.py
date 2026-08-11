from abc import ABC, abstractmethod


class ShowtimePricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, base_price, seat_number):
        pass


class BasePricingStrategy(ShowtimePricingStrategy):
    def calculate_price(self, base_price, seat_number):
        return base_price


class VIPRowPricingStrategy(ShowtimePricingStrategy):
    """Adds a premium for back rows (e.g., Row E, F)"""

    def calculate_price(self, base_price, seat_number):
        if seat_number.startswith("E") or seat_number.startswith("F"):
            return base_price + 5.0
        return base_price
