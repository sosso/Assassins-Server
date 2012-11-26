from game_constants import DEFAULT_STARTING_MONEY
from sqlalchemy import Column, Integer, VARCHAR, INTEGER
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, scoped_session
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import String, Boolean
import logging
import dbutils
import os

if bool(os.environ.get('TEST_RUN', False)):
    engine = create_engine('mysql://anthony:password@localhost:3306/test_assassins', echo=False, pool_recycle=3600)#recycle connection every hour to prevent overnight disconnect)
else:
    engine = create_engine('mysql://bfc1ffabdb36c3:65da212b@us-cdbr-east-02.cleardb.com/heroku_1cec684f35035ce', echo=True, pool_recycle=3600)#recycle connection every hour to prevent overnight disconnect)

Base = declarative_base(bind=engine)
sm = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Session = scoped_session(sm)
logging.basicConfig()

def clear_all():
    for table in reversed(Base.metadata.sorted_tables):
        engine.execute(table.delete())


class User(Base):
    __tablename__ = 'user'
    logger = logging.getLogger('User')
    #column definitions
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    username = Column(u'username', VARCHAR(length=255), nullable=False)
    password = Column(u'password', VARCHAR(length=255), nullable=False)
    profile_picture = Column(u'profile_picture', VARCHAR(length=255), nullable=False)
    
    # association proxy of "user_games" collection
    # to "game" attribute
    games = association_proxy('user_games', 'game')
    
    def User(self, password, username, profile_picture):
        self.username = username
        self.password = password
        self.profile_picture = profile_picture
    
def login(username, password):
    logger = logging.getLogger('login')
    session = Session()
    try:
        users = session.query(User).filter_by(username=username, password=password).all()
        user = session.query(User).filter_by(username=username, password=password).one()
    except Exception, e:
        logger.exception(e)
        user = None
    return user

class Game(Base):
    __tablename__ = 'game'
    #column definitions
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    title = Column(u'title', VARCHAR(length=255), nullable=False)
    password = Column(u'password', VARCHAR(length=255), nullable=False)
    starting_money = Column(u'starting_money', Integer(), nullable=False)
    
    users = association_proxy('game_users', 'user',
                              creator=lambda kw: Keyword(keyword=kw))
    
    def Game(self, password, title, starting_money=DEFAULT_STARTING_MONEY):
        self.title = title
        self.password = password
        self.starting_money = starting_money
        
    def add_users(self, users_list):
        for user in users_list:
            self.add_user(user)
    
    def add_user(self, user):
        self.users.append(user)


class UserGame(Base):
    __tablename__ = 'user_game'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    game_id = Column(Integer, ForeignKey('game.id'), primary_key=True)
    money = Column(Integer, nullable=False)
    alive = Column(Boolean)
    target_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    
    # bidirectional attribute/collection of "user"/"user_game"
    user = relationship(User,
                primaryjoin=(user_id==User.id),
                backref=backref("user_games",
                                cascade="all, delete-orphan")
            )

    # reference to the "Game" object
    game = relationship("Game", 
                        primaryjoin=(game_id==Game.id),
                        backref=backref("game_users", cascade="all, delete-orphan"))
    

    def __init__(self, user_id, item_id, money=DEFAULT_STARTING_MONEY):
        self.user_id = user_id
        self.item_id = item_id

    def __repr__(self):
        return '<UserGame %d @ %d>' % (self.game_id, self.user_id)

        
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

