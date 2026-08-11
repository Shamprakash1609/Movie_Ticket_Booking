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
