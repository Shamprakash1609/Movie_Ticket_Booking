class SeatView:
    """Renders the auditorium for the booking screen."""

    BOOKED_MARK = "[X]"
    AISLE = " " * 4

    @staticmethod
    def display_show_header(details, available, capacity, vip_rows=(), vip_premium=0.0):
        title = details["title"].upper()
        base = details["price"]
        line = "=" * 64
        print(f"\n{line}")
        print(f" 🎬 {title}")
        print(f" 🏛  {details['theater_name']}, {details['city']}  |  📺 {details['screen_name']}")
        print(f" 🕒 {details['start_time']}")
        print(f" 💰 Normal seat: ₹{base:.2f}")
        if vip_rows and vip_premium:
            print(
                f" ⭐ VIP seat (rows {', '.join(vip_rows)}): ₹{base + vip_premium:.2f}"
                f"  —  ₹{vip_premium:.2f} more than a normal seat"
            )
        print(f" 🎟  {available} of {capacity} seats available")
        print(line)

    @classmethod
    def display_layout(
        cls, layout, booked_seats, vip_rows=(), vip_premium=0.0, base_price=None
    ):
        booked = set(booked_seats)
        vip = {r.upper() for r in vip_rows}
        banner_shown = False

        label_width = max(len(seat) for seat in layout.all_seats)
        cell_width = label_width + 3
        gutter = max(len(label) for label, _ in layout.rows) + 2

        aisle_at = layout.cols // 2 if layout.cols >= 8 else None
        grid_width = layout.cols * cell_width + (len(cls.AISLE) if aisle_at else 0)
        pad = " " * gutter

        cls._print_screen_banner(pad, grid_width)

        for label, seats in layout.rows:
            if label in vip and not banner_shown:
                banner_shown = True
                tag = f" VIP ROWS - ₹{vip_premium:.0f} EXTRA PER SEAT "
                print(f"{pad}{tag.center(grid_width, '-')}")

            cells = []
            for index in range(layout.cols):
                if aisle_at is not None and index == aisle_at:
                    cells.append(cls.AISLE)
                if index < len(seats):
                    seat = seats[index]
                    text = cls.BOOKED_MARK if seat in booked else seat
                else:
                    text = ""
                cells.append(text.center(cell_width))
            marker = f"{label}*" if label in vip else label
            print(f"{marker:>{gutter}} {''.join(cells)}  {marker}")

        cls._print_legend(pad, grid_width, sorted(vip), vip_premium, base_price)

    @classmethod
    def _print_screen_banner(cls, pad, grid_width):
        inner = max(grid_width - 4, 20)
        print()
        print(f"{pad}  +{'-' * inner}+")
        print(f"{pad}  |{'S  C  R  E  E  N'.center(inner)}|")
        print(f"{pad}  +{'-' * inner}+")
        print(f"{pad}  {'^  All eyes this way  ^'.center(inner)}")
        print()

    @classmethod
    def _print_legend(cls, pad, grid_width, vip_rows=(), vip_premium=0.0, base_price=None):
        print()
        print(f"{pad}{'-' * grid_width}")
        print(f"{pad}Legend:   A1 = available     {cls.BOOKED_MARK} = already booked")
        if vip_rows and vip_premium:
            print(
                f"{pad}          {', '.join(vip_rows)}* = VIP rows "
                f"(the back rows, best view of the screen)"
            )
            if base_price is not None:
                print(
                    f"{pad}          Normal seat ₹{base_price:.2f}  |  "
                    f"VIP seat ₹{base_price + vip_premium:.2f}  "
                    f"(₹{vip_premium:.2f} extra per VIP seat)"
                )
        print(f"{pad}Seat ID = row letter + seat number (type them exactly as shown).")
        print()
