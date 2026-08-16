import hashlib
import hmac
import math
import re
from datetime import datetime


class Helpers:
    MIN_PASSWORD_LENGTH = 4

    @staticmethod
    def hash_password(password):
        """Hash a password for storing."""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def verify_password(stored_password, provided_password):
        """Verify a stored password against one provided by user"""
        # compare_digest instead of == so the comparison time does not depend on
        # how many leading characters of the hash matched.
        return hmac.compare_digest(
            stored_password or "", Helpers.hash_password(provided_password)
        )

    @staticmethod
    def is_valid_email(email):
        """Validate email using regex."""
        regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(regex, email) is not None

    @staticmethod
    def is_valid_date(date_string, format="%Y-%m-%d"):
        """Check if date matches format."""
        try:
            datetime.strptime(date_string, format)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_valid_datetime(datetime_string, format="%Y-%m-%d %H:%M"):
        """Check if datetime matches format."""
        try:
            datetime.strptime(datetime_string, format)
            return True
        except ValueError:
            return False

    @staticmethod
    def prompt_int(prompt_text, min_val=None, allow_cancel=True):
        """Prompt user for integer input with validation and retry loop."""
        while True:
            val_str = input(prompt_text).strip()
            if allow_cancel and val_str.lower() in ("c", "cancel", "q", "quit"):
                print("Operation cancelled.")
                return None
            try:
                val = int(val_str)
                if min_val is not None and val < min_val:
                    print(
                        f"[Input Error] Value must be at least {min_val}. Please try again."
                    )
                    continue
                return val
            except ValueError:
                print(
                    "[Input Error] Invalid input. Please enter a valid integer number (or 'c' to cancel)."
                )

    @staticmethod
    def prompt_float(prompt_text, min_val=None, allow_cancel=True):
        """Prompt user for float input with validation and retry loop."""
        while True:
            val_str = input(prompt_text).strip()
            if allow_cancel and val_str.lower() in ("c", "cancel", "q", "quit"):
                print("Operation cancelled.")
                return None
            try:
                val = float(val_str)
                # float() accepts 'nan'/'inf'; nan compares False against every bound,
                # so it would slip past the min_val check and be stored as a price.
                if not math.isfinite(val):
                    print(
                        "[Input Error] Invalid input. Please enter a valid decimal number (e.g. 12.50) (or 'c' to cancel)."
                    )
                    continue
                if min_val is not None and val < min_val:
                    print(
                        f"[Input Error] Value must be at least {min_val}. Please try again."
                    )
                    continue
                return val
            except ValueError:
                print(
                    "[Input Error] Invalid input. Please enter a valid decimal number (e.g. 12.50) (or 'c' to cancel)."
                )

    @staticmethod
    def prompt_date(prompt_text, allow_cancel=True):
        """Prompt user for date string YYYY-MM-DD with retry loop."""
        while True:
            date_str = input(prompt_text).strip()
            if allow_cancel and date_str.lower() in ("c", "cancel", "q", "quit"):
                print("Operation cancelled.")
                return None
            if Helpers.is_valid_date(date_str):
                return date_str
            print(
                "[Input Error] Invalid date format. Must be YYYY-MM-DD (e.g., 2026-08-25). Please try again."
            )

    @staticmethod
    def prompt_datetime(prompt_text, allow_cancel=True):
        """Prompt user for datetime string YYYY-MM-DD HH:MM with retry loop."""
        while True:
            dt_str = input(prompt_text).strip()
            if allow_cancel and dt_str.lower() in ("c", "cancel", "q", "quit"):
                print("Operation cancelled.")
                return None
            if Helpers.is_valid_datetime(dt_str):
                return dt_str
            print(
                "[Input Error] Invalid date-time format. Must be YYYY-MM-DD HH:MM (e.g., 2026-08-25 18:30). Please try again."
            )

    @staticmethod
    def prompt_non_empty(prompt_text, allow_cancel=True):
        """Prompt user for a non-empty string."""
        while True:
            val_str = input(prompt_text).strip()
            if allow_cancel and val_str.lower() in ("c", "cancel", "q", "quit"):
                print("Operation cancelled.")
                return None
            if val_str:
                return val_str
            print("[Input Error] This field cannot be empty. Please try again.")

    @staticmethod
    def prompt_list_choice(prompt_text, count, allow_back=False):
        """Pick one entry from a numbered list that was just printed.

        Returns the 0-based index, the string 'back' when the user types 'b',
        or None when the user cancels out of the flow entirely.
        """
        hints = ["a number 1-%d" % count if count > 1 else "1"]
        if allow_back:
            hints.append("'b' to go back")
        hints.append("'c' to cancel")

        while True:
            raw = input(prompt_text).strip().lower()
            if raw in ("c", "cancel", "q", "quit"):
                print("Operation cancelled.")
                return None
            if allow_back and raw in ("b", "back"):
                return "back"
            if raw.isdigit() and 1 <= int(raw) <= count:
                return int(raw) - 1
            print(f"[Input Error] Enter {', '.join(hints)}.")

    @staticmethod
    def day_name(date_string):
        """'2026-08-14' -> 'Friday'. Returns '-' if the date can't be parsed."""
        try:
            return datetime.strptime(date_string[:10], "%Y-%m-%d").strftime("%A")
        except (ValueError, TypeError):
            return "-"

    @staticmethod
    def print_table(headers, rows):
        """Prints a nicely formatted ASCII table."""
        if not headers or not rows:
            print("No data available.")
            return

        # Calculate max width for each column
        col_widths = [len(str(header)) for header in headers]
        for row in rows:
            for i, col in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(col)))

        # Create separator
        separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"

        # Print header
        print(separator)
        header_row = (
            "|"
            + "|".join(
                f" {str(headers[i]).ljust(col_widths[i])} " for i in range(len(headers))
            )
            + "|"
        )
        print(header_row)
        print(separator)

        # Print rows
        for row in rows:
            data_row = (
                "|"
                + "|".join(
                    f" {str(row[i]).ljust(col_widths[i])} " for i in range(len(row))
                )
                + "|"
            )
            print(data_row)

        print(separator)

    @staticmethod
    def clear_screen():
        """Clears the console screen."""
        print("\033[H\033[J", end="")
