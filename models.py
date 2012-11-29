from dbutils import get_or_create
from game_constants import DEFAULT_STARTING_MONEY
from sqlalchemy import Column, Integer, VARCHAR, INTEGER
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, scoped_session
from sqlalchemy.orm.session import sessionmaker, object_session
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql.expression import and_
from sqlalchemy.types import String, Boolean, DateTime
import datetime
import dbutils
import logging
import os

if bool(os.environ.get('TEST_RUN', False)):
    engine = create_engine('mysql://anthony:password@127.0.0.1:3306/test_assassins', echo=False, pool_recycle=3600)#recycle connection every hour to prevent overnight disconnect)
else:
    engine = create_engine('mysql://bfc1ffabdb36c3:65da212b@us-cdbr-east-02.cleardb.com/heroku_1cec684f35035ce', echo=True, pool_recycle=3600)#recycle connection every hour to prevent overnight disconnect)

Base = declarative_base(bind=engine)
sm = sessionmaker(bind=engine, autoflush=True, autocommit=False, expire_on_commit=False)
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

class UserGame(Base):
    __tablename__ = 'user_game'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    game_id = Column(Integer, ForeignKey('game.id'), primary_key=True)
    money = Column(Integer, nullable=False)
    alive = Column(Boolean)
    
    user = relationship(User, primaryjoin=User.id == user_id)
    
    def __init__(self, user_id, game_id, money=DEFAULT_STARTING_MONEY, alive=True, target_user_id=None):
        self.user_id = user_id
        self.game_id = game_id
        self.alive = alive
        self.money = money

    def __repr__(self):
        return '<UserGame %d @ %d>' % (self.game_id, self.user_id)
    
class Game(Base):
    __tablename__ = 'game'
    #column definitions
    logger = logging.getLogger('Game')
    id = Column(u'id', INTEGER(), primary_key=True)
    title = Column(u'title', VARCHAR(length=255))
    password = Column(u'password', VARCHAR(length=255))
    starting_money = Column(u'starting_money', Integer())
    max_shot_interval_minutes = Column(Integer(), default=90)
    
    
    def _get_user_list(self):
        access_objects = self._get_user_statuses()
        users_list = []
        for usergame in access_objects:
            users_list.append(usergame.user)
        return users_list
    user_list = property(_get_user_list)
    
    def _get_user_statuses(self):
        return object_session(self).query(UserGame).filter_by(game_id=self.id).all()
    user_statuses = property(_get_user_statuses)
    
    
    def Game(self, password, title, starting_money=DEFAULT_STARTING_MONEY, max_shot_interval_minutes=90):
        self.title = title
        self.password = password
        self.starting_money = starting_money
        self.max_shot_interval_minutes = max_shot_interval_minutes
        
    def add_users(self, users_list):
        for user in users_list:
            self.add_user(user)
    
    def add_user(self, user):
        get_or_create(Session(), UserGame, user_id=user.id, game_id=self.id)
        Session.flush()
        
    def get_users(self):
        return Session().query(UserGame).filter_by(game_id=self.id).all()
    
    def mission_completed(self, mission):
        #validate the mission belongs to this game
        if mission.game_id == self.id:
            pass
            #Get the target's mission to reassign it to the assassin
            targets_mission = object_session(self).query(Mission).filter_by(game_id=self.id, assassin_id=mission.target_id, completed_timestamp=None).one()
            if targets_mission.target_id == mission.assassin_id: #meaning the players in question were targeting each other, and that the game should probably be over
                self.game_over()
            else:
                self.reassign_mission(targets_mission)
        else:
            raise Exception("Supplied mission does not belong to this game!")
    
    #TODO stub
    def game_over(self):
        pass
        
    def reassign_mission(self, new_assassin_user, mission_to_reassign):
        #create a new mission with the proper assassin and target
        reassigned_mission = Mission(assassin_id=new_assassin_user.id, target_id=mission_to_reassign.target_id, game_id=self.id)
        session = object_session(self)
        try:
            session.add(reassigned_mission)
            session.flush()
            session.commit()
        except Exception, e:
            session.rollback()
            self.logger.exception(e)

# I don't know that we need a separate class for this.  Shot can probably encapsulate it just fine?
# But maybe we archive this?
#class Kill(Base):
#    __tablename__ = 'kill'
#
#    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
#
#    game_id = Column(Integer, ForeignKey('game.id'), primary_key=True)
#    assassin_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
#    target_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
#    
#    kill_picture_url = Column(String(255), nullable=False)
#    validation_picture = Column(String(255), nullable=True)
#    assassin_gps = Column(String(255), nullable=True)
#    target_gps = Column(String(255), nullable=True)
#    timestamp = Column(DateTime, default=datetime.datetime.now)
#    confirmed = Column(Boolean, default=False)
#    
#    def __init__(self, assassin_id, game_id, target_id, kill_picture_url, validation_picture=None, assassin_gps=None, target_gps=None):
#        self.assassin_id = assassin_id
#        self.game_id = game_id
#        self.target_id = target_id
#        self.kill_picture_url = kill_picture_url
#        self.validation_picture = validation_picture
#        self.assassin_gps = assassin_gps
#        self.target_gps = target_gps
#
#    def __repr__(self):
#        return '<UserGame %d @ %d>' % (self.game_id, self.user_id)

class Mission(Base):
    __tablename__ = 'mission'
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)

    game_id = Column(Integer, ForeignKey('game.id'), primary_key=True)
    assassin_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    target_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    
    #None until it's associated with a kill
    kill_id = Column(Integer, ForeignKey('kill.id'), nullable=True)
    
    assignment_timestamp = Column(DateTime, default=datetime.datetime.now)
    completed_timestamp = Column(DateTime, nullable=True)
    
    def __init__(self, assassin_id, game_id, target_id):
        self.assassin_id = assassin_id
        self.game_id = game_id
        self.target_id = target_id
    
    def set_kill_id(self, kill_id):
        self.kill_id = kill_id

    def __repr__(self):
        return '<UserGame %d @ %d>' % (self.game_id, self.user_id)



class Shot(Base):
    __tablename__ = 'shot'
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    
    game_id = Column(Integer, ForeignKey('game.id'), primary_key=True)
    assassin_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    target_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    
    kill_id = Column(Integer, ForeignKey('kill.id'), nullable=True)
    shot_picture_url = Column(String(255), nullable=False)
    assassin_gps= Column(String(255), nullable=True)
    
    timestamp = Column(DateTime, default=datetime.datetime.now)
    
    def __init__(self, assassin_id, target_id, game_id, shot_picture, assassin_gps=None, timestamp=datetime.datetime.now):
        self.assassin_id = assassin_id
        self.target_id = target_id
        self.game_id = game_id
        self.shot_picture_url = shot_picture
        self.assassin_gps = assassin_gps
        self.timestamp = timestamp

    def set_kill_id(self, kill_id):
        self.kill_id = kill_id

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


