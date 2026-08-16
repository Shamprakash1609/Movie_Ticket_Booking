from abc import ABC, abstractmethod

from Modules.Movies.MovieModel import Movie
from Modules.Movies.MovieDAO import MovieDAO


class MovieSearchStrategy(ABC):
    @abstractmethod
    def search(self, movie_dao, query_val):
        pass


class SearchByTitleStrategy(MovieSearchStrategy):
    def search(self, movie_dao, title_val):
        query = "SELECT * FROM movies WHERE title LIKE ?"
        return movie_dao.get_by_query(query, (f"%{title_val}%",))


class SearchByGenreStrategy(MovieSearchStrategy):
    def search(self, movie_dao, genre_val):
        query = "SELECT * FROM movies WHERE genre LIKE ?"
        return movie_dao.get_by_query(query, (f"%{genre_val}%",))


class SearchByLanguageStrategy(MovieSearchStrategy):
    def search(self, movie_dao, lang_val):
        query = "SELECT * FROM movies WHERE language = ?"
        return movie_dao.get_by_query(query, (lang_val,))


class SearchByShowDateStrategy(MovieSearchStrategy):
    """Movies with a show still to start on the given date.

    Shows earlier the same day are left out so this matches the date list the
    user picked from, which only counts upcoming shows.
    """

    def search(self, movie_dao, date_val):
        query = """
            SELECT DISTINCT m.* FROM movies m
            JOIN showtimes s ON s.movie_id = m.movie_id
            WHERE DATE(s.start_time) = ?
              AND s.start_time > datetime('now', 'localtime')
            ORDER BY m.title ASC
        """
        return movie_dao.get_by_query(query, (date_val,))


class SearchByTheaterStrategy(MovieSearchStrategy):
    """Movies with upcoming shows at a given theater."""

    def search(self, movie_dao, theater_id):
        query = """
            SELECT DISTINCT m.* FROM movies m
            JOIN showtimes s ON s.movie_id = m.movie_id
            JOIN screens sc ON s.screen_id = sc.screen_id
            WHERE sc.theater_id = ? AND s.start_time > datetime('now', 'localtime')
            ORDER BY m.title ASC
        """
        return movie_dao.get_by_query(query, (theater_id,))


class SearchByReleaseDateStrategy(MovieSearchStrategy):
    """`query_val` is a (from_date, to_date) pair; either side may be None."""

    def search(self, movie_dao, date_range):
        released_from, released_to = date_range
        query = "SELECT * FROM movies WHERE 1 = 1"
        params = []

        if released_from:
            query += " AND release_date >= ?"
            params.append(released_from)
        if released_to:
            query += " AND release_date <= ?"
            params.append(released_to)

        query += " ORDER BY release_date DESC"
        return movie_dao.get_by_query(query, tuple(params))


class CustomFilterStrategy(MovieSearchStrategy):
    """Combines any subset of criteria with AND.

    `query_val` is a dict; every key is optional:
        title, genre, language, min_rating, max_duration,
        released_from, released_to, show_date, theater_id, city.
    """

    SHOW_KEYS = ("show_date", "theater_id", "city")

    def search(self, movie_dao, criteria):
        criteria = criteria or {}
        conditions = []
        params = []

        # Only join the schedule tables when a criterion actually needs them.
        needs_shows = any(criteria.get(k) for k in self.SHOW_KEYS)
        joins = (
            """
            JOIN showtimes s ON s.movie_id = m.movie_id
            JOIN screens sc ON s.screen_id = sc.screen_id
            JOIN theaters t ON sc.theater_id = t.theater_id
            """
            if needs_shows
            else ""
        )

        simple = [
            ("title", "m.title LIKE ?", lambda v: f"%{v}%"),
            ("genre", "m.genre LIKE ?", lambda v: f"%{v}%"),
            ("language", "m.language LIKE ?", lambda v: f"%{v}%"),
            ("min_rating", "m.rating >= ?", lambda v: v),
            ("max_duration", "m.duration <= ?", lambda v: v),
            ("released_from", "m.release_date >= ?", lambda v: v),
            ("released_to", "m.release_date <= ?", lambda v: v),
            ("show_date", "DATE(s.start_time) = ?", lambda v: v),
            ("theater_id", "t.theater_id = ?", lambda v: v),
            ("city", "t.city LIKE ?", lambda v: f"%{v}%"),
        ]

        for key, clause, adapt in simple:
            value = criteria.get(key)
            if value is not None and value != "":
                conditions.append(clause)
                params.append(adapt(value))

        where = " AND ".join(conditions) if conditions else "1 = 1"
        query = f"SELECT DISTINCT m.* FROM movies m {joins} WHERE {where} ORDER BY m.title ASC"
        return movie_dao.get_by_query(query, tuple(params))
