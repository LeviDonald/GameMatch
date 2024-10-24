from app.routes import db
from flask_login import UserMixin



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
