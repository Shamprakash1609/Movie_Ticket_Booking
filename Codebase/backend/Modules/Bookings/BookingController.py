import csv
import os
from datetime import datetime

from Modules.Bookings.BookingService import BookingService
from Modules.Bookings.PricingStrategy import VIPRowPricingStrategy
from Modules.Showtimes.ShowtimeService import ShowtimeService
from Modules.Common.Exceptions import MovieTicketSystemError
from Modules.Common.Helpers import Helpers


class BookingController:
    def __init__(self):
        self.booking_service = BookingService()
        self.showtime_service = ShowtimeService()

    def display_seat_layout(self, all_seats, booked_seats):
        print("\n--- Screen ---")
        current_row = ""
        row_str = ""
        for seat in all_seats:
            if seat[0] != current_row:
                if row_str:
                    print(row_str)
                current_row = seat[0]
                row_str = f"{current_row} | "

            marker = "[X]" if seat in booked_seats else f"[{seat}]"
            row_str += f"{marker} "

        if row_str:
            print(row_str)
        print("\n[X] = Booked | [Seat] = Available\n")

    def book_tickets(self, customer_id):
        print("\n--- Book Tickets ---")
        showtime_id = Helpers.prompt_int("Enter Showtime ID: ", min_val=1)
        if showtime_id is None:
            return

        try:
            all_seats, booked_seats = self.booking_service.generate_seat_matrix(
                showtime_id
            )
            self.display_seat_layout(all_seats, booked_seats)

            while True:
                seats_input = input(
                    "Enter seat numbers separated by commas (e.g., A1, A2, A3) or 'c' to cancel: "
                ).strip()
                if seats_input.lower() in ("c", "cancel", "q", "quit"):
                    print("Booking cancelled.")
                    return
                selected_seats = [
                    s.strip().upper() for s in seats_input.split(",") if s.strip()
                ]
                if selected_seats:
                    break
                print("[Input Error] Please select at least one seat.")

            num_seats = len(selected_seats)
            print(
                f"\nYou have selected {num_seats} seat(s): {', '.join(selected_seats)}"
            )

            strategy = VIPRowPricingStrategy()
            booking = self.booking_service.book_tickets(
                customer_id, showtime_id, selected_seats, strategy
            )

            print(f"\n[Success] Booking confirmed! Booking ID: {booking.booking_id}")
            print(f"Total Amount Paid: ${booking.total_amount:.2f}")

        except MovieTicketSystemError as e:
            print(f"\n[Error] {str(e)}")

    def view_my_bookings(self, customer_id):
        print("\n--- My Bookings ---")
        print("1. Upcoming Bookings")
        print("2. Past Bookings")
        print("3. All Bookings")

        choice = input("Choice: ").strip()
        if choice not in ["1", "2", "3"]:
            print("[Error] Invalid choice.")
            return

        bookings = self.booking_service.get_customer_bookings(customer_id, choice)

        if not bookings:
            print("No bookings found.")
            return

        headers = ["Booking ID", "Movie", "Start Time", "Seats", "Total ($)", "Status"]
        rows = [
            [
                b["booking_id"],
                b["title"],
                b["start_time"],
                b["seats"],
                f"{b['total_amount']:.2f}",
                b["status"],
            ]
            for b in bookings
        ]
        Helpers.print_table(headers, rows)

    def cancel_booking(self, customer_id):
        print("\n--- Cancel Booking ---")
        booking_id = Helpers.prompt_int("Enter Booking ID to cancel: ", min_val=1)
        if booking_id is None:
            return

        confirm = input("Are you sure you want to cancel this booking? [y/N]: ").strip()
        if confirm.lower() == "y":
            try:
                self.booking_service.cancel_booking(booking_id, customer_id)
                print("[Success] Booking cancelled. Refund initiated.")
            except MovieTicketSystemError as e:
                print(f"[Error] {str(e)}")
        else:
            print("Cancellation aborted.")

    def view_all_bookings_admin(self):
        print("\n--- View All Bookings ---")
        bookings = self.booking_service.get_all_bookings()

        if not bookings:
            print("No bookings found in the system.")
            return

        headers = ["ID", "Customer", "Movie", "Showtime", "Seats", "Total", "Status"]
        rows = [
            [
                b["booking_id"],
                b["username"],
                b["title"],
                b["start_time"],
                b["seats"],
                f"${b['total_amount']:.2f}",
                b["status"],
            ]
            for b in bookings
        ]
        Helpers.print_table(headers, rows)

        export = input("Export to CSV? [y/N]: ")
        if export.lower() == "y":
            self._export_to_csv(headers, rows)

    def _export_to_csv(self, headers, rows):
        export_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "exports"
        )
        os.makedirs(export_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bookings_export_{timestamp}.csv"
        filepath = os.path.join(export_dir, filename)

        try:
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            print(f"[Success] Data exported to {filepath}")
        except IOError as e:
            print(f"[Error] Failed to write CSV: {e}")
