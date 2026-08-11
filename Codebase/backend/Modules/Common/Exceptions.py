class MovieTicketSystemError(Exception):
    """Base exception for the Movie Ticket Booking System"""

    pass


class AuthenticationError(MovieTicketSystemError):
    pass


class RegistrationError(MovieTicketSystemError):
    pass


class InvalidInputError(MovieTicketSystemError):
    pass


class EntityNotFoundError(MovieTicketSystemError):
    pass


class ShowtimeOverlapError(MovieTicketSystemError):
    pass


class SeatAlreadyBookedError(MovieTicketSystemError):
    pass


class CancellationError(MovieTicketSystemError):
    pass


class ActiveBookingsExistError(MovieTicketSystemError):
    pass
