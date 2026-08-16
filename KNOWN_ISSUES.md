# Known Issues & Limitations

An audit of the whole codebase, split into **what was fixed** and **what was deliberately
left alone**. Everything below was confirmed by reading the code and reproducing the
behaviour — nothing here is speculative.

Verified by `python3 tests_regression.py` (212 checks) and `python3 test.py`
(scripted end-to-end CLI walkthrough, 16 asserted outcomes).

---

## Part 1 — Fixed

### Crashes (an uncaught exception killed the CLI)

| # | Where | Problem | Fix |
|---|---|---|---|
| 1 | `Modules/Auth/UserDAO.py` `update()` | `username`/`email` are `UNIQUE`. Editing a profile to a value another account already holds raised a raw `sqlite3.IntegrityError`, which is not a `MovieTicketSystemError`, so every handler missed it and the app died mid-session. | Catch `IntegrityError`, roll back, re-raise as `RegistrationError`. |
| 2 | `Modules/Support/SupportController.py` `manage_profile()` | Had **no `try/except` at all**, so #1 propagated to `Main`. It also mutated the in-memory `user` *before* the DB write, so a failed save left the session holding data that was never persisted. | Wrap both updates; restore the previous field values on failure. |
| 3 | `Modules/Movies/MovieService.py` `delete_movie()` | The guard only counted **CONFIRMED bookings**. A movie with showtimes but no bookings passed the guard, then `DELETE FROM movies` violated `showtimes.movie_id` (no `ON DELETE CASCADE`) → raw `IntegrityError`, uncaught. | Also count showtimes and raise `InvalidInputError`. |
| 4 | `Modules/Bookings/BookingBuilder.py` | `build_booking()` raised `ValueError`, which `except MovieTicketSystemError` does not catch. | Raise `InvalidInputError`. |
| 5 | `Modules/Bookings/PricingStrategy.py` | `BookingController.collect_payment` reads `strategy.vip_rows` / `.premium`, which only `VIPRowPricingStrategy` defined. Passing `BasePricingStrategy` raised `AttributeError` — a Liskov violation. | Give `BasePricingStrategy` `vip_rows = ()` and `premium = 0.0`. |
| 6 | `Modules/Notifications/NotificationService.py` | `detach()` called `list.remove()`, raising `ValueError` for an observer that was never attached, while `attach()` guards. | Guard `detach()` symmetrically. |
| 7 | `Main.py` | Only `KeyboardInterrupt` was handled at the top level; anything else dumped a traceback and lost the session. | Add a last-resort `except Exception` that reports and exits cleanly. |

### Correctness

| # | Where | Problem | Fix |
|---|---|---|---|
| 8 | `Modules/Bookings/BookingController.py` `vip_rows_for()` | `layout.rows[-2:]` on a screen with **2 or fewer rows** returned *every* row, so **every seat was charged the ₹100 VIP premium**. A 12-seat screen billed ₹2400 instead of ₹1200. | Return `[]` when the screen has no more rows than the VIP block. |
| 9 | `Modules/Bookings/PricingStrategy.py` | `tuple(...) if vip_rows else DEFAULT_VIP_ROWS` — an explicitly empty list is falsy, so "no VIP rows" silently became the default rows `E`/`F`. | Test `if vip_rows is None` instead. |
| 10 | `Modules/Showtimes/ShowtimeService.py` | Showtimes could be scheduled **in the past**. Every listing filters `start_time > now`, so the row was invisible in the UI while still occupying its screen slot in `check_overlap` forever. | Reject `start_time <= now`. |
| 11 | `Modules/Bookings/BookingService.py` | A customer could cancel and be refunded **after the show had played**. The original code even carried a comment admitting the check was missing. | Block cancellation once `start_time` has passed. |
| 12 | `Modules/Auth/AuthService.py` | The 4-character password rule lived **only in the controller**; any other caller could create a 1-character password. | Enforce it in the service too, via `Helpers.MIN_PASSWORD_LENGTH`. |
| 13 | `Modules/Common/Helpers.py` `prompt_float()` | `float()` accepts `nan`/`inf`, and `nan < min_val` is `False`, so `nan` passed validation and could be stored as a ticket price. | Reject non-finite values with `math.isfinite`. |
| 14 | `Modules/Theaters/TheaterController.py` | At the `Save this theater? [Y/n]` prompt, typing **`yes` cancelled the save** (`"yes" != "y"`), discarding everything just entered. | Accept `y` and `yes`. |
| 15 | `Modules/Theaters/TheaterController.py` | The city filter was not `.strip()`ed, so a stray space searched for `'% %'`. | Strip it. |

### Data integrity & security

| # | Where | Problem | Fix |
|---|---|---|---|
| 16 | `Db_utils.py` `__new__` | `_instance` was published **before** `_init_connection` ran, so a failed init cached a half-built object for the rest of the process. | Assign only after the connection succeeds. |
| 17 | `Db_utils.py` `close()` | Closed the connection but left `_instance` set, so the next `DatabaseConnectionManager()` returned a closed object. | Clear `_instance`. |
| 18 | `Db_utils.py` `_create_tables()` | Swallowed `sqlite3.Error`, letting the app boot on a half-created schema and fail later with confusing "no such table" errors. | Re-raise after rollback. |
| 19 | `Db_utils.py` | The seeded `admin` account — the most privileged in the system — was created with **no audit row**. | Write an `audit_logs` entry alongside it. |
| 20 | `Modules/Common/Helpers.py` `verify_password()` | Compared hashes with `==`, which short-circuits and leaks timing information. | Use `hmac.compare_digest`. |
| 21 | `Modules/Bookings/BookingController.py` `_export_to_csv()` | `open(..., "w")` with no encoding; rows contain `₹` (U+20B9), which the default Windows encoding (cp1252) cannot represent → `UnicodeEncodeError` killed the export. | Pass `encoding="utf-8"`. |

### Testing

| # | Where | Problem | Fix |
|---|---|---|---|
| 22 | `test.py` | Printed **"COMPLETED SUCCESSFULLY" for any `SystemExit`** and asserted nothing. Its keystroke script was written for an older booking flow, so every booking step desynced — it produced 0 bookings and 0 contact requests while still reporting success. | Re-record the script for the 5-step wizard and assert on 16 expected outcomes, forbidden strings (tracebacks, raw `sqlite3.` errors), and final row counts. Exits non-zero on failure. |
| 23 | `tests_regression.py` *(new)* | No unit-level safety net existed. | 212 checks across Helpers, SeatLayout, Auth, Theaters, Movies + all 7 search strategies, Showtimes overlap boundaries, Bookings, cancellation, pricing, notifications, the singleton, and a full scripted CLI run. |

Both suites were validated by deliberately breaking `cancel_booking` and confirming they fail.

---

## Part 2 — Known limitations, deliberately not fixed

These are real, but each needs a schema change, a new dependency, or a design decision —
none qualifies as a minimal fix.

### 1. No database constraint prevents double-booking a seat

`booking_seats` has **no unique index**. The rule "one confirmed booking per seat per
showtime" exists only in Python. `book_tickets` re-reads the booked seats before writing,
which is why it holds for this single-process CLI, but two concurrent processes could both
pass the check.

**Why not fixed:** a plain `UNIQUE(showtime_id, seat_number)` would *also* block re-booking
a seat freed by a cancellation, because `cancel_booking` keeps the seat rows and only flips
`bookings.status`. Verified:

```
INSERT bs(1,1,'A1')   -- booked, then cancelled
INSERT bs(2,1,'A1')   -- someone re-books the freed seat
=> UNIQUE constraint failed
```

A correct constraint needs `showtime_id` **and** status denormalised onto `booking_seats`
plus a partial index, and the cancel paths updated to maintain them — a design change.

### 2. Passwords are unsalted SHA-256, and every database ships with `admin` / `admin`

SHA-256 is fast by design, which is exactly wrong for passwords, and no salt means identical
passwords produce identical hashes. The seeded admin is never forced to change its password.

**Why not fixed:** correct handling needs `bcrypt` or `argon2`, and the project is
deliberately stdlib-only. Changing the algorithm also invalidates every stored hash.

### 3. Partial cancellation destroys history

`cancel_seats` **hard-deletes** `booking_seats` rows, while `cancel_booking` only flips a
status. After releasing some seats there is no record of what was originally sold or at what
price — and the audit row for it points at the *booking* id under the table name
`booking_seats`, which is a different key space, so it cannot identify the seats either.

**Fix would be:** a `cancelled_at` column instead of a delete.

### 4. The audit log is thin

- **No before/after values** — an `UPDATE` row tells you a movie changed, not what changed.
- **Write-only** — `AuditDAO` has only `insert`; nothing in the app ever `SELECT`s
  `audit_logs`, and there is no admin screen for it.
- **Mutable** — it is an ordinary table; anyone who can write data can rewrite the record.
- **Not transactional** — `AuditDAO.insert` commits on its own, after the change it records.
- **Coverage gaps** — `booking_seats` INSERT, `available_seats` changes and
  `payment_status` transitions are never logged.
- **No index**, and the table only grows.

### 5. Notifications are a stub

`ConsoleCustomerObserver` is named for the console but writes to `notifications.log`, and
nothing reads that file back. `NotificationService` imports `UserDAO` and `UserRole` and
never uses them — a fossil of the intended per-customer delivery. Each service constructs
its **own** `NotificationService` (it is not a singleton), so "the notification system" is
really several independent ones. `_message` is instance state rather than a `notify()`
parameter, which is why `ShowtimeService` reaches into the private attribute directly.

### 6. Money is stored as `float`

`price REAL` and Python `float`. Binary floating point cannot represent `0.1` exactly, so
sums accumulate error. Production systems use integer paise or `decimal.Decimal`.

### 7. Other known behaviours

| Area | Limitation |
|---|---|
| `MovieDAO.get_all` | Silently caps at 100 movies; the UI reports the truncated count as the total. |
| `SearchByLanguageStrategy` | Uses `language = ?` while title/genre use `LIKE`, so language search is exact-match only — unsignposted in the UI. |
| All `LIKE` searches | `%` and `_` in user input are not escaped, so they act as wildcards. |
| Custom filter "Rating at least" | `rating` is hardcoded to `0.0` on insert and never editable, so any `min_rating > 0` matches nothing. |
| `ShowtimeController.add_showtime` | Collects a theatre ID only to list its screens; the screen ID is never cross-checked against it, so a show can be attached to a screen at a different theatre. |
| Theatres / Showtimes | Insert and read only — no update or delete path exists in the app. |
| `check_overlap` | The second `OR` clause is fully subsumed by the first; harmless but dead. |
| `view_theaters` | N+1 queries — one for theatres plus one per theatre for its screens. |
| Payment | Entirely simulated. "Payment successful" is printed **before** the booking is attempted, and `payment_status` is set to `COMPLETED` unconditionally in a separate transaction after the main commit. |
| Console output | Emoji and `₹` are printed unconditionally; a non-UTF-8 Windows console will raise `UnicodeEncodeError`. |
| `contact_requests` | Created lazily by `SupportDAO`, outside the central schema in `Db_utils` — the schema lives in two places. |
| `get_customer_bookings` | Takes the raw menu keystroke (`'1'`/`'2'`/`'3'`) all the way into the DAO, so renumbering the menu changes the SQL. |
| `get_booked_seats` | Hardcodes the string `'CONFIRMED'` instead of `BookingStatus.CONFIRMED.value`. |
| `BookingStatus.COMPLETED` | Defined but never written by any code path. |
| Emails | Stored and matched case-sensitively, so one mailbox can hold two accounts. |
| Movies / theatres | No uniqueness check — the same record can be inserted repeatedly. |
| Schema | `CREATE TABLE IF NOT EXISTS` never migrates; changing a column requires deleting the database file. |
| `updated_at` | SQLite has no `ON UPDATE`, so every `UPDATE` must set it by hand (the DAOs do). |
