from game_constants import DEFAULT_STARTING_MONEY
from sqlalchemy import Column, Integer, VARCHAR, INTEGER
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, scoped_session
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import String, Boolean
import dbutils
import os

if bool(os.environ.get('TEST_RUN', False)):
    engine = create_engine('mysql://anthony:password@localhost:3306/assassins', echo=True, pool_recycle=3600)#recycle connection every hour to prevent overnight disconnect)
else:
    engine = create_engine('mysql://bfc1ffabdb36c3:65da212b@us-cdbr-east-02.cleardb.com/heroku_1cec684f35035ce', echo=True, pool_recycle=3600)#recycle connection every hour to prevent overnight disconnect)

Base = declarative_base(bind=engine)
sm = sessionmaker(bind=engine, autoflush=True, autocommit=False, expire_on_commit=False)
Session = scoped_session(sm)


class User(Base):
    __tablename__ = 'user'
    #column definitions
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    username = Column(u'username', VARCHAR(length=255), nullable=False)
    password = Column(u'password', VARCHAR(length=255), nullable=False)
    profile_picture = Column(u'profile_picture', VARCHAR(length=255), nullable=False)
    
    def User(self, password, username, profile_picture):
        self.username = username
        self.password = password
        self.profile_picture = profile_picture


class Game(Base):
    __tablename__ = 'game'
    #column definitions
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    title = Column(u'title', VARCHAR(length=255), nullable=False)
    password = Column(u'password', VARCHAR(length=255), nullable=False)
    starting_money = Column(u'starting_money', Integer(), nullable=False)
    
    def Game(self, password, title, starting_money=DEFAULT_STARTING_MONEY):
        self.title = title
        self.password = password
        self.starting_money = starting_money


class UserInGameStatus(Base):
    __tablename__ = 'usergamepermission'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    game_id = Column(Integer, ForeignKey('game.id'), primary_key=True)
    money = Column(Integer, nullable=False)
    alive = Column(Boolean)
    target_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    

    def __init__(self, user_id, item_id, money=DEFAULT_STARTING_MONEY):
        self.user_id = user_id
        self.item_id = item_id

    def __repr__(self):
        return '<UserInGameStatus %d @ %d>' % (self.game_id, self.user_id)


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer)
    description = Column(VARCHAR(length=255))

    def __init__(self, item_id, description=''):
        self.item_id = item_id
        self.description = description

    def __repr__(self):
        return '<Item %d>' % self.item_id

    def serialize(self):
        return {'Item number': self.item_id,
                'Description': self.description
                }

Base.metadata.create_all(engine)


