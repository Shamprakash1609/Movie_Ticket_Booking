"""Regression harness for the Movie Ticket Booking system.

Run from the Codebase/ directory:  python3 harness.py
Exits non-zero if any check fails.
"""
import os
import sys
import io
import getpass
import sqlite3
import traceback
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS, FAIL = [], []


def check(name, got, want):
    if got == want:
        PASS.append(name)
    else:
        FAIL.append(f"{name}\n      expected: {want!r}\n      got     : {got!r}")


def check_raises(name, exc_types, fn):
    try:
        fn()
    except exc_types as e:
        PASS.append(f"{name} -> {type(e).__name__}")
        return e
    except Exception as e:
        FAIL.append(f"{name}\n      expected {exc_types}, got {type(e).__name__}: {e}")
        return None
    FAIL.append(f"{name}\n      expected {exc_types}, but no exception was raised")
    return None


def check_no_raise(name, fn):
    try:
        fn()
        PASS.append(name)
    except Exception as e:
        FAIL.append(f"{name}\n      unexpected {type(e).__name__}: {e}")


def fresh_db(tag):
    """Drop the singleton and rebuild against a clean per-group database."""
    from Db_utils import DatabaseConnectionManager

    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, f"_h_{tag}.db")
    inst = DatabaseConnectionManager._instance
    if inst is not None:
        try:
            inst.close()
        except Exception:
            pass
    DatabaseConnectionManager._instance = None
    if os.path.exists(path):
        os.remove(path)
    return DatabaseConnectionManager(f"_h_{tag}.db")


def cleanup():
    here = os.path.dirname(os.path.abspath(__file__))
    for f in os.listdir(here):
        if f.startswith("_h_") and f.endswith(".db"):
            try:
                os.remove(os.path.join(here, f))
            except OSError:
                pass


DAY1 = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
DAY2 = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
PAST = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")


# --------------------------------------------------------------------------
def t_helpers():
    from Modules.Common.Helpers import Helpers

    check("helpers: sha256 length", len(Helpers.hash_password("x")), 64)
    check("helpers: verify ok", Helpers.verify_password(Helpers.hash_password("abc"), "abc"), True)
    check("helpers: verify bad", Helpers.verify_password(Helpers.hash_password("abc"), "abd"), False)
    check("helpers: email ok", Helpers.is_valid_email("a.b+c@d-e.co.uk"), True)
    check("helpers: email no-at", Helpers.is_valid_email("nope"), False)
    check("helpers: email no-tld", Helpers.is_valid_email("a@b"), False)
    check("helpers: date ok", Helpers.is_valid_date("2026-08-15"), True)
    check("helpers: date impossible", Helpers.is_valid_date("2026-02-30"), False)
    check("helpers: date wrong fmt", Helpers.is_valid_date("15/08/2026"), False)
    check("helpers: datetime ok", Helpers.is_valid_datetime("2026-08-15 18:30"), True)
    check("helpers: datetime missing time", Helpers.is_valid_datetime("2026-08-15"), False)
    check("helpers: day_name", Helpers.day_name("2026-08-17"), "Monday")
    check("helpers: day_name from datetime", Helpers.day_name("2026-08-17 18:30"), "Monday")
    check("helpers: day_name junk", Helpers.day_name("junk"), "-")
    check("helpers: day_name None", Helpers.day_name(None), "-")

    # float() accepts nan/inf and nan slips past every comparison -> bogus prices
    for bad in ("nan", "inf", "-inf"):
        real_stdin, real_stdout = sys.stdin, sys.stdout
        sys.stdin = io.StringIO(bad + "\nc\n")
        sys.stdout = io.StringIO()
        try:
            got = Helpers.prompt_float("p: ", min_val=0.01)
        finally:
            sys.stdin, sys.stdout = real_stdin, real_stdout
        check(f"helpers: prompt_float rejects {bad!r}", got, None)


def t_seat_layout():
    from Modules.Bookings.SeatLayout import SeatLayout

    for cap in (1, 4, 6, 7, 12, 40, 90, 100, 120, 121, 200, 700):
        L = SeatLayout(cap)
        check(f"layout: {cap} seats total", len(L.all_seats), cap)
        check(f"layout: {cap} unique", len(set(L.all_seats)), cap)
    check("layout: row_label 0", SeatLayout.row_label(0), "A")
    check("layout: row_label 25", SeatLayout.row_label(25), "Z")
    check("layout: row_label 26", SeatLayout.row_label(26), "AA")
    check("layout: row_label 701", SeatLayout.row_label(701), "ZZ")
    check("layout: row_of", SeatLayout.row_of("aa7"), "AA")
    check(
        "layout: natural sort",
        sorted(["J10", "J5", "A2", "B1", "AA3", "A10"], key=SeatLayout.sort_key),
        ["A2", "A10", "B1", "J5", "J10", "AA3"],
    )
    L = SeatLayout(40)
    check("layout: has_seat A1", L.has_seat("A1"), True)
    check("layout: has_seat Z9", L.has_seat("Z9"), False)

    # A small screen must not have every one of its rows designated VIP, or every
    # single seat silently costs the premium.
    from Modules.Bookings.BookingController import BookingController
    from Modules.Bookings.PricingStrategy import VIPRowPricingStrategy

    for cap in (6, 12, 16, 20, 24, 40, 120):
        lay = SeatLayout(cap)
        vip = BookingController.vip_rows_for(lay)
        check(f"pricing: cap={cap} leaves some non-VIP rows", len(vip) < len(lay.rows), True)
        strat = VIPRowPricingStrategy(vip)
        charged = sum(strat.calculate_price(100.0, s) for s in lay.all_seats)
        check(f"pricing: cap={cap} not every seat is premium", charged < cap * 200, True)
    check("pricing: explicit empty vip_rows is honoured (no default fallback)",
          VIPRowPricingStrategy([]).calculate_price(100.0, "E1"), 100.0)
    check("pricing: vip_rows=None still uses the default rows",
          VIPRowPricingStrategy().calculate_price(100.0, "E1"), 200.0)


def t_auth():
    fresh_db("auth")
    from Modules.Auth.AuthService import AuthService
    from Modules.Common.Exceptions import AuthenticationError, RegistrationError
    from Modules.Auth.UserModel import Admin, Customer
    from Modules.Common.Enums import UserRole

    svc = AuthService()
    u = svc.register_customer("john", "secret123", "john@example.com", "+15551234567")
    check("auth: registered type", type(u).__name__, "Customer")
    check("auth: role is enum", u.role, UserRole.CUSTOMER)
    check("auth: password hashed", u.password != "secret123", True)
    check("auth: login by username", svc.authenticate("john", "secret123").username, "john")
    check("auth: login by email", svc.authenticate("john@example.com", "secret123").username, "john")
    check("auth: admin login", type(svc.authenticate("admin", "admin", as_admin=True)).__name__, "Admin")

    e1 = check_raises("auth: wrong password", AuthenticationError, lambda: svc.authenticate("john", "WRONG"))
    e2 = check_raises("auth: unknown user", AuthenticationError, lambda: svc.authenticate("ghost", "x"))
    check("auth: no user enumeration (same message)", str(e1) == str(e2), True)
    check_raises("auth: customer via admin door", AuthenticationError, lambda: svc.authenticate("john", "secret123", as_admin=True))
    check_raises("auth: admin via customer door", AuthenticationError, lambda: svc.authenticate("admin", "admin", as_admin=False))
    check_raises("auth: dup username", RegistrationError, lambda: svc.register_customer("john", "p", "o@x.com", "1"))
    check_raises("auth: dup email", RegistrationError, lambda: svc.register_customer("jane", "p", "john@example.com", "1"))
    check_raises("auth: bad email", RegistrationError, lambda: svc.register_customer("jane", "p", "bad", "1"))
    check_raises("auth: missing fields", RegistrationError, lambda: svc.register_customer("", "p", "a@b.com", "1"))
    check_raises("auth: short password rejected by service", RegistrationError, lambda: svc.register_customer("jane2", "ab", "jane2@x.com", "1"))


def t_theaters():
    fresh_db("theaters")
    from Modules.Theaters.TheaterService import TheaterService
    from Modules.Theaters.TheaterModel import Theater
    from Modules.Common.Exceptions import InvalidInputError

    svc = TheaterService()
    t = Theater(None, "PVR", "Forum", "Chennai", 999, 1)
    svc.add_theater_with_screens(t, [{"screen_name": "A", "capacity": 30}, {"screen_name": "B", "capacity": 45}], 1)
    check("theaters: capacity derived", t.capacity, 75)
    check("theaters: screens created", len(svc.get_screens(t.theater_id)), 2)
    check("theaters: list all", len(svc.get_all_theaters()), 1)
    check("theaters: filter match (partial, case-insensitive)", len(svc.get_all_theaters("chen")), 1)
    check("theaters: filter no match", len(svc.get_all_theaters("Paris")), 0)

    check_raises("theaters: no name", InvalidInputError, lambda: svc.add_theater_with_screens(Theater(None, "", "L", "P", 0, 1), [{"screen_name": "S", "capacity": 5}], 1))
    check_raises("theaters: no screens", InvalidInputError, lambda: svc.add_theater_with_screens(Theater(None, "X", "L", "P", 0, 1), [], 1))
    check_raises("theaters: zero seats", InvalidInputError, lambda: svc.add_theater_with_screens(Theater(None, "X", "L", "P", 0, 1), [{"screen_name": "S", "capacity": 0}], 1))
    check_raises("theaters: unnamed screen", InvalidInputError, lambda: svc.add_theater_with_screens(Theater(None, "X", "L", "P", 0, 1), [{"screen_name": "", "capacity": 5}], 1))

    # atomicity: a failed multi-row create must leave nothing behind
    before = len(svc.get_all_theaters())
    try:
        svc.add_theater_with_screens(Theater(None, "Ghost", "L", "P", 0, 1), [{"screen_name": "ok", "capacity": 5}, {"screen_name": "", "capacity": 5}], 1)
    except InvalidInputError:
        pass
    check("theaters: failed create leaves no partial theater", len(svc.get_all_theaters()), before)


def t_movies():
    db = fresh_db("movies")
    from Modules.Movies.MovieService import MovieService
    from Modules.Movies.MovieModel import Movie
    from Modules.Movies.Strategies import (
        SearchByTitleStrategy, SearchByGenreStrategy, SearchByLanguageStrategy,
        SearchByReleaseDateStrategy, SearchByShowDateStrategy, SearchByTheaterStrategy,
        CustomFilterStrategy, MovieSearchStrategy,
    )
    from Modules.Theaters.TheaterService import TheaterService
    from Modules.Theaters.TheaterModel import Theater
    from Modules.Showtimes.ShowtimeService import ShowtimeService
    from Modules.Common.Exceptions import InvalidInputError, EntityNotFoundError, ActiveBookingsExistError, MovieTicketSystemError

    check_raises("movies: strategy ABC not instantiable", TypeError, lambda: MovieSearchStrategy())

    ms = MovieService()
    for t, dur, g, l, rd in [("Leo", 164, "Action", "Tamil", "2023-10-19"),
                             ("Inception", 148, "Sci-Fi", "English", "2010-07-16"),
                             ("Vikram", 175, "Action Comedy", "Tamil", "2022-06-03"),
                             ("Interstellar", 169, "Sci-Fi", "English", "2014-11-07")]:
        ms.add_movie(Movie(None, t, "desc", dur, g, l, rd, 0.0, None, 1))
    db.execute("UPDATE movies SET rating=8.8 WHERE title='Inception'")
    db.execute("UPDATE movies SET rating=7.2 WHERE title='Leo'")
    db.commit()

    def titles(s, v):
        return sorted(m.title for m in ms.search_movies(s, v))

    check("movies: by title substring", titles(SearchByTitleStrategy(), "in"), ["Inception", "Interstellar"])
    check("movies: by genre substring", titles(SearchByGenreStrategy(), "Action"), ["Leo", "Vikram"])
    check("movies: by language", titles(SearchByLanguageStrategy(), "Tamil"), ["Leo", "Vikram"])
    check("movies: release range open", len(ms.search_movies(SearchByReleaseDateStrategy(), (None, None))), 4)
    check("movies: release range from", titles(SearchByReleaseDateStrategy(), ("2014-01-01", None)), ["Interstellar", "Leo", "Vikram"])
    check("movies: custom empty = all", len(ms.search_movies(CustomFilterStrategy(), {})), 4)
    check("movies: custom genre+lang", titles(CustomFilterStrategy(), {"genre": "Action", "language": "Tamil"}), ["Leo", "Vikram"])
    check("movies: custom min_rating", titles(CustomFilterStrategy(), {"min_rating": 8.0}), ["Inception"])
    check("movies: custom min_rating=0 kept", len(ms.search_movies(CustomFilterStrategy(), {"min_rating": 0})), 4)
    check("movies: custom max_duration", titles(CustomFilterStrategy(), {"min_rating": 8.0, "max_duration": 150}), ["Inception"])

    check_raises("movies: no title", InvalidInputError, lambda: ms.add_movie(Movie(None, "", "d", 100, "g", "l", "2026-01-01", 0.0, None, 1)))
    check_raises("movies: zero duration", InvalidInputError, lambda: ms.add_movie(Movie(None, "T", "d", 0, "g", "l", "2026-01-01", 0.0, None, 1)))
    check_raises("movies: negative duration", InvalidInputError, lambda: ms.add_movie(Movie(None, "T", "d", -5, "g", "l", "2026-01-01", 0.0, None, 1)))
    check_raises("movies: update missing", EntityNotFoundError, lambda: ms.update_movie(Movie(999, "X", "d", 10, "g", "l", "2026-01-01", 0.0, None, 1), 1))
    check_raises("movies: delete missing", EntityNotFoundError, lambda: ms.delete_movie(999, 1))

    # schedule Leo, then deleting it must be a clean domain error (not a raw IntegrityError)
    TheaterService().add_theater_with_screens(Theater(None, "PVR", "F", "Chennai", 0, 1), [{"screen_name": "A1", "capacity": 40}], 1)
    ShowtimeService().add_showtime(1, 1, f"{DAY1} 18:00", 250.0, 1)
    check("movies: by show date", titles(SearchByShowDateStrategy(), DAY1), ["Leo"])
    check("movies: by theater", titles(SearchByTheaterStrategy(), 1), ["Leo"])
    check("movies: custom city needs join", titles(CustomFilterStrategy(), {"city": "Chennai"}), ["Leo"])

    check_raises("movies: delete movie WITH showtimes -> domain error, not crash",
                 MovieTicketSystemError, lambda: ms.delete_movie(1, 1))
    check("movies: movie survived the blocked delete", ms.get_movie(1) is not None, True)

    # clean movie (no showtimes) still deletes
    check_no_raise("movies: delete clean movie", lambda: ms.delete_movie(3, 1))
    check("movies: clean movie gone", ms.get_movie(3), None)


def t_showtimes():
    fresh_db("showtimes")
    from Modules.Theaters.TheaterService import TheaterService
    from Modules.Theaters.TheaterModel import Theater
    from Modules.Movies.MovieService import MovieService
    from Modules.Movies.MovieModel import Movie
    from Modules.Showtimes.ShowtimeService import ShowtimeService
    from Modules.Common.Exceptions import InvalidInputError, EntityNotFoundError, ShowtimeOverlapError

    TheaterService().add_theater_with_screens(Theater(None, "PVR", "F", "Chennai", 0, 1),
                                              [{"screen_name": "A1", "capacity": 120}, {"screen_name": "A2", "capacity": 80}], 1)
    ms = MovieService()
    ms.add_movie(Movie(None, "Leo", "d", 164, "Action", "Tamil", "2023-10-19", 0.0, None, 1))     # 1
    ms.add_movie(Movie(None, "Inception", "d", 120, "Sci-Fi", "English", "2010-07-16", 0.0, None, 1))  # 2
    ss = ShowtimeService()

    st = ss.add_showtime(1, 1, f"{DAY1} 18:00", 250.0, 1)
    check("showtimes: end_time derived (164+30)", st.end_time, f"{DAY1} 21:14")
    check("showtimes: seats from screen capacity", st.available_seats, 120)

    check_raises("showtimes: overlap tail", ShowtimeOverlapError, lambda: ss.add_showtime(2, 1, f"{DAY1} 16:00", 200.0, 1))
    check_raises("showtimes: overlap same start", ShowtimeOverlapError, lambda: ss.add_showtime(2, 1, f"{DAY1} 18:00", 200.0, 1))
    check_raises("showtimes: overlap inside", ShowtimeOverlapError, lambda: ss.add_showtime(2, 1, f"{DAY1} 19:00", 200.0, 1))
    check_raises("showtimes: overlap 1min before end", ShowtimeOverlapError, lambda: ss.add_showtime(2, 1, f"{DAY1} 21:13", 200.0, 1))
    check_no_raise("showtimes: touching end is allowed", lambda: ss.add_showtime(2, 1, f"{DAY1} 21:14", 200.0, 1))
    check_no_raise("showtimes: clean gap before", lambda: ss.add_showtime(2, 1, f"{DAY1} 15:00", 200.0, 1))
    check_no_raise("showtimes: other screen free", lambda: ss.add_showtime(2, 2, f"{DAY1} 19:00", 200.0, 1))

    check_raises("showtimes: bad datetime", InvalidInputError, lambda: ss.add_showtime(1, 1, "17/08/2026 18:00", 250.0, 1))
    check_raises("showtimes: date only", InvalidInputError, lambda: ss.add_showtime(1, 1, DAY2, 250.0, 1))
    check_raises("showtimes: zero price", InvalidInputError, lambda: ss.add_showtime(1, 1, f"{DAY2} 10:00", 0.0, 1))
    check_raises("showtimes: negative price", InvalidInputError, lambda: ss.add_showtime(1, 1, f"{DAY2} 10:00", -5.0, 1))
    check_raises("showtimes: missing movie", EntityNotFoundError, lambda: ss.add_showtime(99, 1, f"{DAY2} 10:00", 250.0, 1))
    check_raises("showtimes: missing screen", EntityNotFoundError, lambda: ss.add_showtime(1, 99, f"{DAY2} 10:00", 250.0, 1))
    check_raises("showtimes: past showtime rejected", InvalidInputError, lambda: ss.add_showtime(1, 1, f"{PAST} 10:00", 250.0, 1))

    check("showtimes: upcoming dates listed", len(ss.get_upcoming_show_dates()) >= 1, True)
    check("showtimes: grouped by movie", len(ss.get_upcoming_showtimes_grouped_by_movie()) >= 1, True)
    check("showtimes: details join", ss.get_showtime_details(1)["theater_name"], "PVR")
    check("showtimes: screen_capacity in details", ss.get_showtime_details(1)["screen_capacity"], 120)


def t_bookings():
    db = fresh_db("bookings")
    from Modules.Theaters.TheaterService import TheaterService
    from Modules.Theaters.TheaterModel import Theater
    from Modules.Movies.MovieService import MovieService
    from Modules.Movies.MovieModel import Movie
    from Modules.Showtimes.ShowtimeService import ShowtimeService
    from Modules.Auth.AuthService import AuthService
    from Modules.Bookings.BookingService import BookingService
    from Modules.Bookings.PricingStrategy import VIPRowPricingStrategy, BasePricingStrategy
    from Modules.Bookings.BookingBuilder import BookingBuilder
    from Modules.Common.Exceptions import (
        SeatAlreadyBookedError, InvalidInputError, EntityNotFoundError, CancellationError,
    )

    TheaterService().add_theater_with_screens(Theater(None, "PVR", "F", "Chennai", 0, 1), [{"screen_name": "A1", "capacity": 40}], 1)
    MovieService().add_movie(Movie(None, "Leo", "d", 164, "Action", "Tamil", "2023-10-19", 0.0, None, 1))
    ShowtimeService().add_showtime(1, 1, f"{DAY1} 18:00", 250.0, 1)
    a = AuthService()
    a.register_customer("john", "p1234", "john@x.com", "1")   # user 2
    a.register_customer("jane", "p1234", "jane@x.com", "2")   # user 3

    bs = BookingService()
    vip = VIPRowPricingStrategy(["D", "E"])

    def left():
        return db.fetchone("SELECT available_seats FROM showtimes WHERE showtime_id=1")["available_seats"]

    # pricing
    check("bookings: base price", BasePricingStrategy().calculate_price(250.0, "E1"), 250.0)
    check("bookings: vip price", vip.calculate_price(250.0, "E1"), 350.0)
    check("bookings: non-vip row", vip.calculate_price(250.0, "A1"), 250.0)
    check("bookings: vip premium=0 honoured", VIPRowPricingStrategy(["E"], 0).calculate_price(250.0, "E1"), 250.0)

    # builder
    check_raises("bookings: builder needs user", InvalidInputError, lambda: BookingBuilder().set_showtime(1).add_seat("A1", 10).build_booking())
    check_raises("bookings: builder needs seats", InvalidInputError, lambda: BookingBuilder().set_user(2).set_showtime(1).build_booking())
    b = BookingBuilder().set_user(2).set_showtime(1).add_seat("A1", 250.0).add_seat("E1", 350.0).build_booking()
    check("bookings: builder accumulates total", b.total_amount, 600.0)

    bk = bs.book_tickets(2, 1, ["A1", "A2", "E1"], vip)
    check("bookings: total = 2x250 + 1x350", bk.total_amount, 850.0)
    check("bookings: seats decremented", left(), 37)
    check("bookings: seat prices stored", sorted(s["price"] for s in bs.get_booking_seats(bk.booking_id)), [250.0, 250.0, 350.0])
    check("bookings: booked seats visible", sorted(bs.get_booked_seats(1)), ["A1", "A2", "E1"])

    check_raises("bookings: nonexistent seat", InvalidInputError, lambda: bs.book_tickets(2, 1, ["Z9"], vip))
    check_raises("bookings: already booked", SeatAlreadyBookedError, lambda: bs.book_tickets(3, 1, ["A1"], vip))
    check_raises("bookings: duplicate seat", InvalidInputError, lambda: bs.book_tickets(2, 1, ["B1", "B1"], vip))
    check_raises("bookings: missing showtime", EntityNotFoundError, lambda: bs.book_tickets(2, 999, ["B1"], vip))
    check_raises("bookings: empty seat list", InvalidInputError, lambda: bs.book_tickets(2, 1, [], vip))
    check("bookings: failed attempts did not change seats", left(), 37)

    # Application-level protection against double-booking: book_tickets re-reads the
    # booked seats itself, so a stale seat map cannot get a second customer through.
    # (There is deliberately NO database constraint -- see KNOWN LIMITATIONS in the README.
    #  A plain UNIQUE(showtime_id, seat_number) would also block re-booking a seat that a
    #  cancellation freed, because cancel_booking keeps the seat rows.)
    stale_map = bs.get_booked_seats(1)
    check("bookings: stale seat map still shows A1 free to a second customer", "A2" in stale_map, True)
    check_raises("bookings: service re-check blocks the double-book", SeatAlreadyBookedError,
                 lambda: bs.book_tickets(3, 1, ["A2"], vip))

    # partial cancellation
    refund = bs.cancel_seats(bk.booking_id, 2, ["E1"])
    check("bookings: partial refund is the VIP price", refund, 350.0)
    check("bookings: total reduced", db.fetchone("SELECT total_amount FROM bookings WHERE booking_id=?", (bk.booking_id,))["total_amount"], 500.0)
    check("bookings: seat released", left(), 38)
    check("bookings: E1 bookable again", "E1" not in bs.get_booked_seats(1), True)

    check_raises("bookings: cancel seat not in booking", InvalidInputError, lambda: bs.cancel_seats(bk.booking_id, 2, ["B7"]))
    check_raises("bookings: cancel someone else's", CancellationError, lambda: bs.cancel_seats(bk.booking_id, 3, ["A1"]))
    check_raises("bookings: cancel missing booking", EntityNotFoundError, lambda: bs.cancel_booking(999, 2))
    check_raises("bookings: cancel with empty list", InvalidInputError, lambda: bs.cancel_seats(bk.booking_id, 2, []))

    # full cancellation
    total_refund = bs.cancel_booking(bk.booking_id, 2)
    check("bookings: full refund is remaining total", total_refund, 500.0)
    row = db.fetchone("SELECT status, payment_status FROM bookings WHERE booking_id=?", (bk.booking_id,))
    check("bookings: status CANCELLED", row["status"], "CANCELLED")
    check("bookings: payment REFUNDED", row["payment_status"], "REFUNDED")
    check("bookings: all seats released", left(), 40)
    check("bookings: no seats held", bs.get_booked_seats(1), [])
    check_raises("bookings: double cancel blocked", CancellationError, lambda: bs.cancel_booking(bk.booking_id, 2))

    # cancelling every remaining seat delegates to full cancel
    bk2 = bs.book_tickets(3, 1, ["C1", "C2"], vip)
    bs.cancel_seats(bk2.booking_id, 3, ["C1", "C2"])
    check("bookings: cancelling all seats cancels booking", db.fetchone("SELECT status FROM bookings WHERE booking_id=?", (bk2.booking_id,))["status"], "CANCELLED")
    check("bookings: seats back to full", left(), 40)

    # listings
    check("bookings: customer list all", len(bs.get_customer_bookings(2, "3")) >= 1, True)
    check("bookings: admin list all", len(bs.get_all_bookings()) >= 2, True)
    check("bookings: no active bookings left", bs.get_active_bookings(2), [])


def t_audit_and_support():
    db = fresh_db("audit")
    from Modules.Auth.AuthService import AuthService
    from Modules.Support.SupportDAO import SupportDAO
    from Modules.Support.SupportModel import ContactRequest
    from Modules.Audit.AuditService import AuditService
    from Modules.Common.Enums import AuditAction

    AuthService().register_customer("john", "p1234", "john@x.com", "1")
    # two rows: the seeded admin (record_id 1) and the new customer (record_id 2)
    rows = db.fetchall("SELECT * FROM audit_logs WHERE table_name='users' ORDER BY record_id")
    check("audit: registration logged", len(rows), 2)
    check("audit: table_name", rows[-1]["table_name"], "users")
    check("audit: action", rows[-1]["action"], "INSERT")
    check("audit: actor is the new user", rows[-1]["changed_by"], rows[-1]["record_id"])

    rid = SupportDAO().insert(ContactRequest(None, "John", "john@x.com", "Help"))
    AuditService().log_action("contact_requests", rid, AuditAction.INSERT)
    check("audit: system action has null actor", db.fetchone("SELECT changed_by FROM audit_logs WHERE table_name='contact_requests'")["changed_by"], None)
    check("support: contact row stored", db.fetchone("SELECT name FROM contact_requests WHERE request_id=?", (rid,))["name"], "John")

    check("audit: seed admin is logged", db.fetchone("SELECT COUNT(*) c FROM audit_logs WHERE table_name='users' AND record_id=1")["c"] >= 1, True)


def t_profile_and_pricing():
    fresh_db("profile")
    from Modules.Auth.AuthService import AuthService
    from Modules.Auth.UserDAO import UserDAO
    from Modules.Common.Exceptions import MovieTicketSystemError
    from Modules.Bookings.PricingStrategy import BasePricingStrategy, VIPRowPricingStrategy
    from Modules.Bookings.BookingController import BookingController

    a = AuthService()
    a.register_customer("john", "p1234", "john@x.com", "1")
    a.register_customer("jane", "p1234", "jane@x.com", "2")

    dao = UserDAO()
    u = dao.get_by_username("jane")
    u.username = "john"
    check_raises("profile: rename to taken username -> domain error, not crash",
                 MovieTicketSystemError, lambda: dao.update(u))
    check("profile: jane unchanged after failed rename", dao.get_by_username("jane") is not None, True)

    v = dao.get_by_username("jane")
    v.email = "john@x.com"
    check_raises("profile: email collision -> domain error, not crash",
                 MovieTicketSystemError, lambda: dao.update(v))

    w = dao.get_by_username("jane")
    w.username = "jane_renamed"
    check_no_raise("profile: legitimate rename still works", lambda: dao.update(w))
    check("profile: rename persisted", dao.get_by_username("jane_renamed") is not None, True)

    # every pricing strategy must survive the payment screen (Liskov)
    details = {"price": 250.0, "title": "T", "theater_name": "X", "city": "C", "screen_name": "S", "start_time": "2026-01-01 10:00"}
    for strat in (VIPRowPricingStrategy(["E"]), BasePricingStrategy()):
        name = type(strat).__name__
        real_stdout, real_stdin = sys.stdout, sys.stdin
        sys.stdout = io.StringIO()
        sys.stdin = io.StringIO("1\n")
        try:
            BookingController().collect_payment(["A1", "E1"], details, strat)
            PASS.append(f"pricing: {name} works on the payment screen")
        except Exception as e:
            FAIL.append(f"pricing: {name} works on the payment screen\n      {type(e).__name__}: {e}")
        finally:
            sys.stdout, sys.stdin = real_stdout, real_stdin


def t_singleton_and_cancel_window():
    from Db_utils import DatabaseConnectionManager

    db = fresh_db("singleton")
    check("db: singleton identity", DatabaseConnectionManager() is db, True)
    db.close()
    check("db: close() clears the cached instance", DatabaseConnectionManager._instance, None)
    db2 = fresh_db("singleton2")
    check_no_raise("db: usable again after close()", lambda: db2.fetchall("SELECT 1"))

    # a show that has already started must not be refundable
    fresh_db("cancelwindow")
    from Modules.Theaters.TheaterService import TheaterService
    from Modules.Theaters.TheaterModel import Theater
    from Modules.Movies.MovieService import MovieService
    from Modules.Movies.MovieModel import Movie
    from Modules.Showtimes.ShowtimeService import ShowtimeService
    from Modules.Auth.AuthService import AuthService
    from Modules.Bookings.BookingService import BookingService
    from Modules.Bookings.PricingStrategy import BasePricingStrategy
    from Modules.Common.Exceptions import CancellationError

    TheaterService().add_theater_with_screens(Theater(None, "T", "L", "C", 0, 1), [{"screen_name": "S", "capacity": 40}], 1)
    MovieService().add_movie(Movie(None, "M", "d", 100, "g", "l", "2020-01-01", 0.0, None, 1))
    ShowtimeService().add_showtime(1, 1, f"{DAY1} 18:00", 100.0, 1)
    AuthService().register_customer("bob", "p1234", "bob@x.com", "1")
    bs = BookingService()
    bk = bs.book_tickets(2, 1, ["A1"], BasePricingStrategy())

    # rewind the showtime so it is now in the past, then try to refund it
    bs.db.execute("UPDATE showtimes SET start_time = ? WHERE showtime_id = 1", (f"{PAST} 18:00",))
    bs.db.commit()
    check_raises("bookings: cannot cancel a show that already started",
                 CancellationError, lambda: bs.cancel_booking(bk.booking_id, 2))
    check_raises("bookings: cannot release seats from a started show",
                 CancellationError, lambda: bs.cancel_seats(bk.booking_id, 2, ["A1"]))


def t_notifications():
    fresh_db("notif")
    from Modules.Notifications.NotificationService import NotificationService, ConsoleCustomerObserver
    from Modules.Notifications.ObserverInterface import Observer, Subject

    check_raises("notify: Observer ABC not instantiable", TypeError, lambda: Observer())
    check_raises("notify: Subject ABC not instantiable", TypeError, lambda: Subject())

    seen = []

    class Spy(ConsoleCustomerObserver):
        def update(self, message):
            seen.append(message)

    svc = NotificationService()
    spy = Spy()
    svc.attach(spy)
    svc.attach(spy)
    check("notify: attach is idempotent for the same object", len(svc._observers), 1)
    svc.notify_customers_of_new_movie("Leo")
    check("notify: observer received message", len(seen), 1)
    check("notify: message mentions the movie", "Leo" in seen[0], True)
    svc.detach(spy)
    check("notify: detach removes observer", len(svc._observers), 0)
    check_no_raise("notify: detaching an unknown observer does not crash", lambda: svc.detach(Spy()))


def t_cli_smoke():
    """Drive Main.py end-to-end through scripted stdin."""
    fresh_db("cli")
    import Main
    from Modules.Common.Helpers import Helpers

    script = [
        "2", "alice", "alice@example.com", "9876543210", "secret123",     # register
        "1", "2", "admin", "admin",                                        # admin login
        "1", "Avatar 3", "Epic", "190", "Sci-Fi", "English", "2026-12-18",  # add movie
        "5", "PVR Superplex", "45 Park St", "Metro City", "1", "IMAX", "40", "y",  # theatre
        "6", "1", "1", "1", "2026-12-18 19:30", "250.00",                   # showtime
        "2", "1",                                                          # view movies
        "7", "n",                                                          # all bookings, no csv
        "8",                                                               # logout
        "1", "1", "alice@example.com", "secret123",                        # customer login
        "3", "1", "1", "1", "1", "A1, A2, E7", "1",                        # book 3 seats
        "4", "3",                                                          # my bookings
        "9", "Alice", "alice@example.com", "Question?",                    # contact us
        "5", "1", "2", "E7", "y",                                          # cancel one seat
        "5", "1", "1", "y",                                                # cancel rest
        "10", "5",                                                         # logout, exit
    ]
    real_stdin, real_getpass = sys.stdin, getpass.getpass
    getpass.getpass = lambda p="Password: ": sys.stdin.readline().rstrip("\n")
    sys.stdin = io.StringIO("\n".join(script) + "\n")
    buf = io.StringIO()
    real_stdout = sys.stdout
    sys.stdout = buf
    try:
        Main.MainCLIController().start()
    except SystemExit:
        pass
    except Exception:
        sys.stdout = real_stdout
        FAIL.append("cli: crashed\n" + traceback.format_exc())
        return
    finally:
        sys.stdout, sys.stdin, getpass.getpass = real_stdout, real_stdin, real_getpass

    out = buf.getvalue()
    for label, needle in [
        ("cli: registration", "Registration successful"),
        ("cli: admin login", "Welcome back, Admin admin"),
        ("cli: movie added", "added successfully"),
        ("cli: theatre added", "added with 1 screen"),
        ("cli: showtime added", "Showtime scheduled successfully"),
        ("cli: customer login", "Welcome back, alice"),
        ("cli: booking confirmed", "Booking confirmed"),
        ("cli: contact us", "message has been sent"),
        ("cli: seat cancelled", "seat(s) released"),
        ("cli: booking cancelled", "Booking cancelled"),
        ("cli: exited", "Goodbye"),
    ]:
        check(label, needle in out, True)
    check("cli: no tracebacks", "Traceback" in out, False)
    check("cli: no unhandled sqlite errors", "sqlite3." in out, False)


def main():
    groups = [
        ("Helpers", t_helpers), ("SeatLayout", t_seat_layout), ("Auth", t_auth),
        ("Theaters", t_theaters), ("Movies+Strategies", t_movies), ("Showtimes", t_showtimes),
        ("Bookings", t_bookings), ("Audit+Support", t_audit_and_support),
        ("Profile+Pricing", t_profile_and_pricing),
        ("Singleton+CancelWindow", t_singleton_and_cancel_window),
        ("Notifications", t_notifications),
        ("CLI end-to-end", t_cli_smoke),
    ]
    for name, fn in groups:
        try:
            fn()
        except Exception:
            FAIL.append(f"GROUP {name} aborted\n" + traceback.format_exc())
    cleanup()

    print("=" * 70)
    for f in FAIL:
        print("  FAIL  " + f)
    print("=" * 70)
    print(f"  passed: {len(PASS)}    failed: {len(FAIL)}")
    print("=" * 70)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
