import csv
import os
from datetime import datetime

from Modules.Bookings.BookingService import BookingService
from Modules.Bookings.PricingStrategy import VIPRowPricingStrategy
from Modules.Bookings.SeatLayout import SeatLayout
from Modules.Bookings.SeatView import SeatView
from Modules.Showtimes.ShowtimeService import ShowtimeService
from Modules.Common.Exceptions import MovieTicketSystemError
from Modules.Common.Helpers import Helpers


class BookingController:
    # Dummy payment options - nothing is stored, this is a checkout simulation.
    PAYMENT_METHODS = {
        "1": "UPI",
        "2": "Credit / Debit Card",
        "3": "Net Banking",
    }

    def __init__(self):
        self.booking_service = BookingService()
        self.showtime_service = ShowtimeService()

    def collect_payment(self, selected_seats, details, strategy):
        """Shows the bill and asks for a payment method. Returns the method, or None."""
        base = details["price"]
        count = len(selected_seats)
        vip_seats = [
            s for s in selected_seats if SeatLayout.row_of(s) in strategy.vip_rows
        ]
        total = sum(strategy.calculate_price(base, s) for s in selected_seats)

        print("\n--- Payment ---")
        print(f"  Seats ({count}): {', '.join(selected_seats)}")
        print(f"  Tickets       : ₹{base:.2f} x {count} = ₹{base * count:.2f}")
        if vip_seats:
            print(
                f"  VIP premium   : ₹{strategy.premium:.2f} x {len(vip_seats)} "
                f"= ₹{strategy.premium * len(vip_seats):.2f}"
            )
        print(f"  {'-' * 38}")
        print(f"  TOTAL PAYABLE : ₹{total:.2f}")

        print("\nSelect Payment Method:")
        for key, name in self.PAYMENT_METHODS.items():
            print(f"  {key}. {name}")

        while True:
            choice = input("\nEnter payment option (or 'c' to cancel): ").strip()
            if choice.lower() in ("c", "cancel", "q", "quit"):
                print("Payment cancelled. No booking was made.")
                return None

            method = self.PAYMENT_METHODS.get(choice)
            if method:
                break
            print(
                f"[Input Error] Enter {', '.join(self.PAYMENT_METHODS)} "
                "or 'c' to cancel."
            )

        reference = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"\nProcessing ₹{total:.2f} via {method}...")
        print(f"[Success] Payment successful via {method}. Reference: {reference}")
        return method

    VIP_ROW_COUNT = 2

    @classmethod
    def vip_rows_for(cls, layout):
        """The back rows of the screen are the VIP rows.

        A screen with no more rows than the VIP block gets none, otherwise every
        seat in a small auditorium would be charged the premium.
        """
        if len(layout.rows) <= cls.VIP_ROW_COUNT:
            return []
        return [label for label, _ in layout.rows[-cls.VIP_ROW_COUNT:]]

    def display_seat_layout(self, layout, booked_seats, details, strategy):
        available = layout.capacity - len(booked_seats)
        SeatView.display_show_header(
            details, available, layout.capacity, strategy.vip_rows, strategy.premium
        )
        SeatView.display_layout(
            layout,
            booked_seats,
            strategy.vip_rows,
            strategy.premium,
            details["price"],
        )

    def _pick_movie(self, movies):
        print("\n🎬 STEP 1 of 4 — NOW SHOWING")
        Helpers.print_table(
            ["#", "Movie", "Genre", "Language", "Duration", "Theatres", "Shows"],
            [
                [
                    i + 1,
                    m["title"],
                    m["genre"],
                    m["language"],
                    f"{m['duration']} mins",
                    m["theater_count"],
                    m["show_count"],
                ]
                for i, m in enumerate(movies)
            ],
        )
        return Helpers.prompt_list_choice("Select a movie (#): ", len(movies))

    def _pick_theater(self, movie, theaters):
        print(f"\n🏛  STEP 2 of 4 — '{movie['title'].upper()}' is playing at:")
        Helpers.print_table(
            ["#", "Theatre", "Location", "City", "Screens", "Shows", "Next Show"],
            [
                [
                    i + 1,
                    t["theater_name"],
                    t["location"],
                    t["city"],
                    t["screen_count"],
                    t["show_count"],
                    t["next_show"],
                ]
                for i, t in enumerate(theaters)
            ],
        )
        return Helpers.prompt_list_choice(
            "Select a theatre (#): ", len(theaters), allow_back=True
        )

    def _pick_date(self, movie, theater, dates):
        print(
            f"\n📅 STEP 3 of 4 — '{movie['title']}' at {theater['theater_name']}, "
            f"{theater['city']}"
        )
        rows = [
            [i + 1, d["show_date"], Helpers.day_name(d["show_date"]), d["show_count"]]
            for i, d in enumerate(dates)
        ]
        # "All dates" only earns a row when there is more than one date to merge.
        if len(dates) > 1:
            rows.append(
                [len(dates) + 1, "All dates", "-", sum(d["show_count"] for d in dates)]
            )
        Helpers.print_table(["#", "Date", "Day", "Shows"], rows)
        return Helpers.prompt_list_choice(
            "Select a date (#): ", len(rows), allow_back=True
        )

    def _pick_screen(self, movie, theater, screens):
        print(
            f"\n📺 STEP 4a — '{movie['title']}' runs on {len(screens)} screens "
            f"at {theater['theater_name']}"
        )
        Helpers.print_table(
            ["#", "Screen", "Shows", "First Show", "Price From"],
            [
                [
                    i + 1,
                    sc["screen_name"],
                    len(sc["shows"]),
                    sc["shows"][0]["start_time"],
                    f"₹{min(s['price'] for s in sc['shows']):.2f}",
                ]
                for i, sc in enumerate(screens)
            ],
        )
        return Helpers.prompt_list_choice(
            "Select a screen (#): ", len(screens), allow_back=True
        )

    def _pick_time(self, movie, theater, screen):
        print(
            f"\n⏰ STEP 4 of 4 — {movie['title']} | {theater['theater_name']} "
            f"| {screen['screen_name']}"
        )
        Helpers.print_table(
            ["#", "Start Time", "Day", "Price", "Seats Left"],
            [
                [
                    i + 1,
                    s["start_time"],
                    Helpers.day_name(s["start_time"]),
                    f"₹{s['price']:.2f}",
                    s["available_seats"],
                ]
                for i, s in enumerate(screen["shows"])
            ],
        )
        return Helpers.prompt_list_choice(
            "Select a show time (#): ", len(screen["shows"]), allow_back=True
        )

    @staticmethod
    def _group_by_screen(shows):
        """Collapses a flat showtime list into one entry per screen."""
        screens = {}
        for s in shows:
            screen = screens.setdefault(
                s["screen_id"], {"screen_name": s["screen_name"], "shows": []}
            )
            screen["shows"].append(s)
        return list(screens.values())

    def _select_show(self):
        """Walks the customer through Movie -> Theatre -> Date -> Screen -> Time.

        Only one decision is on screen at a time; 'b' steps back, 'c' quits.
        Returns the chosen showtime_id, or None if the customer backed out.
        """
        movies = self.showtime_service.get_movies_with_upcoming_shows()
        if not movies:
            print("No upcoming showtimes are available to book right now.")
            return None

        movie = theater = date = screen = None
        multi_screen = False
        step = "movie"

        while True:
            if step == "movie":
                choice = self._pick_movie(movies)
                if choice is None:
                    return None
                movie = movies[choice]
                step = "theater"

            elif step == "theater":
                theaters = self.showtime_service.get_theaters_for_movie(
                    movie["movie_id"]
                )
                if not theaters:
                    print(f"\n'{movie['title']}' has no upcoming shows any more.")
                    step = "movie"
                    continue

                choice = self._pick_theater(movie, theaters)
                if choice is None:
                    return None
                if choice == "back":
                    step = "movie"
                    continue
                theater = theaters[choice]
                step = "date"

            elif step == "date":
                dates = self.showtime_service.get_movie_show_dates_at_theater(
                    movie["movie_id"], theater["theater_id"]
                )
                if not dates:
                    print("\nNo upcoming shows left at this theatre.")
                    step = "theater"
                    continue

                choice = self._pick_date(movie, theater, dates)
                if choice is None:
                    return None
                if choice == "back":
                    step = "theater"
                    continue
                # The extra row past the last date is the "All dates" option.
                date = None if choice == len(dates) else dates[choice]["show_date"]
                step = "screen"

            elif step == "screen":
                shows = self.showtime_service.get_movie_showtimes_at_theater(
                    movie["movie_id"], theater["theater_id"], date
                )
                if not shows:
                    print("\nNo shows found for that selection.")
                    step = "date"
                    continue

                screens = self._group_by_screen(shows)
                multi_screen = len(screens) > 1
                if not multi_screen:
                    screen = screens[0]
                    step = "time"
                    continue

                choice = self._pick_screen(movie, theater, screens)
                if choice is None:
                    return None
                if choice == "back":
                    step = "date"
                    continue
                screen = screens[choice]
                step = "time"

            elif step == "time":
                choice = self._pick_time(movie, theater, screen)
                if choice is None:
                    return None
                if choice == "back":
                    step = "screen" if multi_screen else "date"
                    continue
                return screen["shows"][choice]["showtime_id"]

    def book_tickets(self, customer_id):
        print("\n--- Book Tickets ---")
        showtime_id = self._select_show()
        if showtime_id is None:
            return

        try:
            layout, booked_seats, details = self.booking_service.generate_seat_matrix(
                showtime_id
            )
            strategy = VIPRowPricingStrategy(self.vip_rows_for(layout))
            self.display_seat_layout(layout, booked_seats, details, strategy)

            if len(booked_seats) >= layout.capacity:
                print("[Error] This show is fully booked.")
                return

            first_seat, last_seat = layout.all_seats[0], layout.all_seats[-1]
            while True:
                seats_input = input(
                    f"Enter seat numbers separated by commas ({first_seat}..{last_seat}, "
                    "e.g., A1, A2, A3) or 'c' to cancel: "
                ).strip()
                if seats_input.lower() in ("c", "cancel", "q", "quit"):
                    print("Booking cancelled.")
                    return

                selected_seats = [
                    s.strip().upper().replace(" ", "")
                    for s in seats_input.split(",")
                    if s.strip()
                ]
                if not selected_seats:
                    print("[Input Error] Please select at least one seat.")
                    continue

                unknown = [s for s in selected_seats if not layout.has_seat(s)]
                if unknown:
                    print(
                        f"[Input Error] No such seat(s): {', '.join(unknown)}. "
                        f"This screen has seats {first_seat} to {last_seat}."
                    )
                    continue

                taken = [s for s in selected_seats if s in booked_seats]
                if taken:
                    print(f"[Input Error] Already booked: {', '.join(taken)}.")
                    continue

                if len(set(selected_seats)) != len(selected_seats):
                    print("[Input Error] You entered the same seat more than once.")
                    continue

                break

            num_seats = len(selected_seats)
            print(
                f"\nYou have selected {num_seats} seat(s): {', '.join(selected_seats)}"
            )

            method = self.collect_payment(selected_seats, details, strategy)
            if method is None:
                return

            booking = self.booking_service.book_tickets(
                customer_id, showtime_id, selected_seats, strategy
            )

            print(f"\n[Success] Booking confirmed! Booking ID: {booking.booking_id}")
            print(f"🎬 Movie   : {details['title']}")
            print(
                f"🏛  Theatre : {details['theater_name']}, {details['location']}, "
                f"{details['city']}"
            )
            print(f"📺 Screen  : {details['screen_name']}")
            print(f"🕒 Show    : {details['start_time']}")
            print(f"🎟  Seats   : {', '.join(selected_seats)}")
            print(f"💰 Paid    : ₹{booking.total_amount:.2f} via {method}")

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

        headers = [
            "Booking ID",
            "Movie",
            "Theatre",
            "City",
            "Screen",
            "Start Time",
            "Seats",
            "Total (₹)",
            "Status",
        ]
        rows = [
            [
                b["booking_id"],
                b["title"],
                b["theater_name"],
                b["city"],
                b["screen_name"],
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

        active = self.booking_service.get_active_bookings(customer_id)
        if not active:
            print("You have no active bookings to cancel.")
            return

        print("\nYour Active Bookings:")
        Helpers.print_table(
            ["Booking ID", "Movie", "Theater", "Screen", "Start Time", "Seats", "Total (₹)"],
            [
                [
                    b["booking_id"],
                    b["title"],
                    b["theater_name"],
                    b["screen_name"],
                    b["start_time"],
                    b["seats"],
                    f"{b['total_amount']:.2f}",
                ]
                for b in active
            ],
        )

        valid_ids = {b["booking_id"] for b in active}
        print("(Type 'c' to go back)")
        while True:
            booking_id = Helpers.prompt_int("Enter Booking ID to cancel: ", min_val=1)
            if booking_id is None:
                return
            if booking_id in valid_ids:
                break
            print(f"[Input Error] #{booking_id} is not one of your active bookings.")

        seats = self.booking_service.get_booking_seats(booking_id)
        booked_seats = [s["seat_number"] for s in seats]
        print(f"\nBooking #{booking_id} holds {len(booked_seats)} seat(s): {', '.join(booked_seats)}")

        print("\n1. Cancel the entire booking")
        print("2. Cancel only some seats")
        print("3. Back")
        choice = input("Choice: ").strip()

        try:
            if choice == "1":
                confirm = input(
                    f"Cancel all {len(booked_seats)} seat(s)? [y/N]: "
                ).strip()
                if confirm.lower() != "y":
                    print("Cancellation aborted.")
                    return

                refund = self.booking_service.cancel_booking(booking_id, customer_id)
                print(f"[Success] Booking cancelled. Refund of ₹{refund:.2f} initiated.")

            elif choice == "2":
                selected = self._prompt_seats_to_cancel(booked_seats)
                if selected is None:
                    return

                confirm = input(
                    f"Cancel {len(selected)} seat(s) — {', '.join(selected)}? [y/N]: "
                ).strip()
                if confirm.lower() != "y":
                    print("Cancellation aborted.")
                    return

                refund = self.booking_service.cancel_seats(
                    booking_id, customer_id, selected
                )
                remaining = [s for s in booked_seats if s not in selected]
                print(
                    f"[Success] {len(selected)} seat(s) released. "
                    f"Refund of ₹{refund:.2f} initiated."
                )
                print(
                    f"Booking #{booking_id} now holds: {', '.join(remaining)}"
                    if remaining
                    else f"Booking #{booking_id} is now fully cancelled."
                )

            elif choice == "3":
                return
            else:
                print("[Error] Invalid choice.")

        except MovieTicketSystemError as e:
            print(f"[Error] {str(e)}")

    def _prompt_seats_to_cancel(self, booked_seats):
        while True:
            raw = input(
                f"Enter seats to cancel from [{', '.join(booked_seats)}] "
                "separated by commas, or 'c' to go back: "
            ).strip()
            if raw.lower() in ("c", "cancel", "q", "quit"):
                print("Cancellation aborted.")
                return None

            selected = [
                s.strip().upper().replace(" ", "") for s in raw.split(",") if s.strip()
            ]
            if not selected:
                print("[Input Error] Please enter at least one seat.")
                continue

            unknown = [s for s in selected if s not in booked_seats]
            if unknown:
                print(
                    f"[Input Error] {', '.join(unknown)} not part of this booking. "
                    "Please try again."
                )
                continue

            if len(set(selected)) != len(selected):
                print("[Input Error] You listed the same seat more than once.")
                continue

            return selected

    def view_all_bookings_admin(self):
        print("\n--- View All Bookings ---")
        bookings = self.booking_service.get_all_bookings()

        if not bookings:
            print("No bookings found in the system.")
            return

        headers = [
            "ID",
            "Customer",
            "Movie",
            "Theater",
            "Screen",
            "Showtime",
            "Seats",
            "Total",
            "Status",
        ]
        rows = [
            [
                b["booking_id"],
                b["username"],
                b["title"],
                b["theater_name"],
                b["screen_name"],
                b["start_time"],
                b["seats"],
                f"₹{b['total_amount']:.2f}",
                b["status"],
            ]
            for b in bookings
        ]
        Helpers.print_table(headers, rows)

        confirmed = [b for b in bookings if b["status"] == "CONFIRMED"]
        revenue = sum(b["total_amount"] for b in confirmed)
        print(
            f"\n{len(bookings)} booking(s) | {len(confirmed)} confirmed "
            f"| Revenue: ₹{revenue:.2f}"
        )

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
            # encoding is explicit because the rows contain the rupee sign, which the
            # default Windows encoding (cp1252) cannot represent.
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            print(f"[Success] Data exported to {filepath}")
        except IOError as e:
            print(f"[Error] Failed to write CSV: {e}")
