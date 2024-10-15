from app.routes import db
from flask_login import UserMixin
# from sqlalchemy import create_engine

# db.engine = create_engine('sqlite:///gamematch.db')


# Setting up tables to be used with SQLAlchemy
# class Users(db.Model, UserMixin):
#     """users SQLAlchemy Table"""
#     __table__ = db.Table('user', db.metadata, autoload_with=db.engine)

#     def get_id(self):
#         return self.username


# class FavouriteGames(db.Model):
#     """favourite_games SQLAlchemy Table"""
#     __table__ = db.Table('favourite_games', db.metadata, autoload_with=db.engine)


# class Games(db.Model):
#     """games SQLAlchemy Table"""
#     __table__ = db.Table('games', db.metadata, autoload_with=db.engine)


# class Categories(db.Model):
#     """categories SQLAlchemy Table"""
#     __table__ = db.Table('categorys', db.metadata, autoload_with=db.engine)

#     def __str__(self):
#         return self.category_name


# class Genres(db.Model):
#     """genres SQLAlchemy Table"""
#     __table__ = db.Table('genres', db.metadata, autoload_with=db.engine)

#     def __str__(self):
#         return self.genre_name


# class Publishers(db.Model):
#     """publishers SQLAlchemy Table"""
#     __table__ = db.Table('publishers', db.metadata, autoload_with=db.engine)


# class Developers(db.Model):
#     """developers SQLAlchemy Table"""
#     __table__ = db.Table('developers', db.metadata, autoload_with=db.engine)


# class GameCat(db.Model):
#     """game_category SQLAlchemy Table"""
#     __table__ = db.Table('game_category', db.metadata, autoload_with=db.engine)


# class GameGen(db.Model):
#     """game_genre SQLAlchemy Table"""
#     __table__ = db.Table('game_genre', db.metadata, autoload_with=db.engine)


# class GamePub(db.Model):
#     """game_publisher SQLAlchemy Table"""
#     __table__ = db.Table('game_publisher', db.metadata, autoload_with=db.engine)


# class GameDev(db.Model):
#     """game_developer SQLAlchemy Table"""
#     __table__ = db.Table('game_developer', db.metadata, autoload_with=db.engine)


class Users(db.Model, UserMixin):
    """users SQLAlchemy Table"""
    __table__ = db.Model.metadata.tables['user']

    def get_id(self):
        return self.username


class FavouriteGames(db.Model):
    """favourite_games SQLAlchemy Table"""
    __table__ = db.Model.metadata.tables['favourite_games']


class Games(db.Model):
    """games SQLAlchemy Table"""
    __table__ = db.Model.metadata.tables['games']


class Categories(db.Model):
    """categories SQLAlchemy Table"""
    __table__ = db.Model.metadata.tables['categorys']

    def __str__(self):
        return self.category_name


class Genres(db.Model):
    """genres SQLAlchemy Table"""
    __table__ = db.Model.metadata.tables['genres']

    def __str__(self):
        return self.genre_name


class Publishers(db.Model):
    """publishers SQLAlchemy Table"""
    __table__ = db.Model.metadata.tables['publishers']


class Developers(db.Model):
    """developers SQLAlchemy Table"""
    __table__ = db.Model.metadata.tables['developers']


class GameCat(db.Model):
    """game_category SQLAlchemy Table"""
    __table__ = db.Model.metadata.tables['game_category']


class GameGen(db.Model):
    """game_genre SQLAlchemy Table"""
    __table__ = db.Model.metadata.tables['game_genre']


class GamePub(db.Model):
    """game_publisher SQLAlchemy Table"""
    __table__ = db.Model.metadata.tables['game_publisher']


class GameDev(db.Model):
    """game_developer SQLAlchemy Table"""
    __table__ = db.Model.metadata.tables['game_developer']
