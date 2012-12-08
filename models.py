from dbutils import get_or_create
from game_constants import DEFAULT_STARTING_MONEY, MAX_SHOT_INTERVAL_MINUTES, \
    MAX_SHOTS_PER_24_HOURS
from passlib.handlers.sha2_crypt import sha256_crypt
from sqlalchemy import Column, Integer, VARCHAR, INTEGER
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, scoped_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import sessionmaker, object_session
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import String, Boolean, DateTime
import datetime
import imgur
import logging
import os
#from passlib.hash import sha256_crypt

if bool(os.environ.get('TEST_RUN', False)):
    engine = create_engine('mysql://anthony:password@127.0.0.1:3306/test_assassins', echo=False, pool_recycle=3600)#recycle connection every hour to prevent overnight disconnect)
else:
    engine = create_engine('mysql://bfc1ffabdb36c3:65da212b@us-cdbr-east-02.cleardb.com/heroku_1cec684f35035ce', echo=False, pool_recycle=3600)#recycle connection every hour to prevent overnight disconnect)

Base = declarative_base(bind=engine)
sm = sessionmaker(bind=engine, autoflush=True, autocommit=False, expire_on_commit=False)
Session = scoped_session(sm)
logging.basicConfig()

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
    
    def __init__(self, password, username, profile_picture):
        self.username = username
        self.password = sha256_crypt.encrypt(password)
        self.profile_picture = profile_picture

    def get_shots_remaining(self, game_id):
        shots = get_shots_since(datetime.datetime.now() - datetime.timedelta(days=1), self.id, game_id, valid_only=True)
        usergame = get_usergame(self.id, game_id)
        return int(usergame.max_shots_per_24_hours - len(shots))
    
    def set_password(self, password):
        self.password = sha256_crypt.encrypt(password)
    
    def valid_password(self, password):
        return sha256_crypt.verify(password, self.password)

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
    
    def get_api_response_dict(self):
        target = get_user(user_id=self.target_id)
        response_dict = {'target_username':target.username, \
                'profile_picture':target.profile_picture, \
                'assigned': self.assignment_timestamp.strftime("%Y-%m-%d %H:%M:%S")}
        if self.completed_timestamp is not None:
            response_dict['completed'] = self.completed_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return response_dict

class InvalidGameRosterException(Exception): "Must have two or more players and 1 game master"

class Game(Base):
    __tablename__ = 'game'
    #column definitions
    logger = logging.getLogger('Game')
    id = Column(INTEGER(), primary_key=True)
    title = Column(VARCHAR(length=255))
    password = Column(VARCHAR(length=255))
    starting_money = Column(Integer())
    max_shot_interval_minutes = Column(Integer(), default=MAX_SHOT_INTERVAL_MINUTES)
    max_shots_per_24_hours = Column(Integer(), default=MAX_SHOTS_PER_24_HOURS)
    started = Column(Boolean(), default=False)
    over = Column(Boolean(), default=False)
    
    def start(self):
        if len(self.get_players()) > 1 and len(self.game_masters) > 0:
            self.assign_initial_missions()
            self.started = True
        else:
            raise InvalidGameRosterException
    
    def _get_game_masters(self):
        access_objects = object_session(self).query(UserGame).filter_by(game_id=self.id, is_game_master=True).all() 
        gm_users = []
        for ao in access_objects:
            gm_users.append(ao.user)
        return gm_users
    game_masters = property(_get_game_masters)
    
    def get_winner(self):
        try:
            players = self.player_statuses
            winner = None
            for player in players:
                if player.alive:
                    if winner is None:
                        winner = player
                    else:
                        winner = None
                        break
        except Exception as e:
            return None
        return winner.user
#    winner = property(_get_winner)
    
    missions = relationship(Mission, primaryjoin=Mission.game_id == id)
    
    def _get_user_list(self):
        access_objects = self._get_user_statuses()
        users_list = []
        for usergame in access_objects:
            users_list.append(usergame.user)
        return users_list
    user_list = property(_get_user_list)
    
    def get_players(self):
        return list(set(self.user_list) - set(self.game_masters))
    
    def _get_user_statuses(self):
        return object_session(self).query(UserGame).filter_by(game_id=self.id).all()
    user_statuses = property(_get_user_statuses)
    
    def _get_player_statuses(self):
        return object_session(self).query(UserGame).filter_by(game_id=self.id, is_game_master=False).all()
    player_statuses = property(_get_player_statuses)
    
    def Game(self, password, title, starting_money=DEFAULT_STARTING_MONEY, max_shot_interval_minutes=90):
        self.title = title
        self.password = password
        self.starting_money = starting_money
        self.max_shot_interval_minutes = max_shot_interval_minutes
        
    def add_users(self, users_list):
        for user in users_list:
            self.add_user(user)
    
    def add_user(self, user, is_game_master=False):
        s = Session()
        get_or_create(s, UserGame, user_id=user.id, game_id=self.id, is_game_master=is_game_master, max_shots_per_24_hours=self.max_shots_per_24_hours, max_shot_interval_minutes=self.max_shot_interval_minutes)
        
    def add_game_master(self, user=None, user_id=None):
        if user is None and user_id is None:
            raise Exception("No user or user_id found")
        elif user is not None and user in self.user_list:
            get_usergame(user.username, self.id).is_game_master = True
        elif user is not None and user not in self.user_list:
            self.add_user(user, True)
        elif user_id is not None:
            get_or_create(Session(), UserGame, user_id=user_id, game_id=self.id)
        
        
    def get_users(self):
        return Session().query(UserGame).filter_by(game_id=self.id).all()
    
    def get_missions(self, active_only=False):
        missions_query = Session().query(Mission).filter_by(game_id=self.id)
        if active_only:
            missions_query = missions_query.filter_by(completed_timestamp=None)
        return missions_query.all()
    
    def assign_initial_missions(self):
        missions = []
        players = self.get_players()
        missions.append(Mission(assassin_id=players[-1].id, target_id=players[0].id, game_id=self.id))
        for index, player in enumerate(players[:-1]):
            missions.append(Mission(assassin_id=player.id, target_id=players[index + 1].id, game_id=self.id))
        s = object_session(self)
        s.add_all(missions)
        s.flush()
        
    
    def mission_completed(self, mission):
        #validate the mission belongs to this game
        if mission.game_id == self.id:
            pass
            #Get the target's mission to reassign it to the assassin
            targets_mission = object_session(self).query(Mission).filter_by(game_id=self.id, assassin_id=mission.target_id, completed_timestamp=None).one()
            mission.completed_timestamp = datetime.datetime.now()

            #Mark the target as dead
            target_usergame = get_usergame(mission.target_id, mission.game_id)
            target_usergame.alive = False
            if targets_mission.target_id == mission.assassin_id: #meaning the players in question were targeting each other, and that the game should probably be over
                self.game_over()
            else:
                self.reassign_mission(new_assassin_id=mission.assassin_id, mission_to_reassign=targets_mission)
        else:
            raise Exception("Supplied mission does not belong to this game!")
    
    #TODO stub
    def game_over(self):
        self.over = True
        
    def reassign_mission(self, new_assassin_id, mission_to_reassign):
        #create a new mission with the proper assassin and target
        reassigned_mission = Mission(assassin_id=new_assassin_id, target_id=mission_to_reassign.target_id, game_id=self.id)
        session = object_session(self)
        try:
            session.add(reassigned_mission)
            session.flush()
            session.commit()
        except Exception, e:
            session.rollback()
            self.logger.exception(e)

class UserGame(Base):
    __tablename__ = 'user_game'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    game_id = Column(Integer, ForeignKey('game.id'), primary_key=True)
    money = Column(Integer, nullable=False)
    alive = Column(Boolean)
    is_game_master = Column(Boolean, default=False, nullable=True)
    max_shot_interval_minutes = Column(Integer(), default=90)
    max_shots_per_24_hours = Column(Integer(), default=3)
    has_body_double = Column(Boolean(), default=False)
    
    user = relationship(User, primaryjoin=User.id == user_id)
    game = relationship(Game, primaryjoin=Game.id == game_id)
    
    def __init__(self, user_id, game_id, money=DEFAULT_STARTING_MONEY, alive=True, target_user_id=None, is_game_master=True, max_shot_interval_minutes=MAX_SHOT_INTERVAL_MINUTES, max_shots_per_24_hours=MAX_SHOTS_PER_24_HOURS):
        self.user_id = user_id
        self.game_id = game_id
        self.alive = alive
        self.money = money
        self.is_game_master = is_game_master

    def __repr__(self):
        return '<UserGame %d @ %d>' % (self.game_id, self.user_id)

    def get_api_response_dict(self):
        response_dict = {'game_id':self.game_id, \
                'game_password':self.game.password, \
                'game_friendly_name': self.game.title, \
                'alive':self.alive}
        response_dict['completed'] = self.completed_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return response_dict
    
# I don't know that we need a separate class for this.  Shot can probably encapsulate it just fine?
# But maybe we archive this?

class Kill(Base):
    __tablename__ = 'kill'

    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)

    game_id = Column(Integer, ForeignKey('game.id'), primary_key=True)
    assassin_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    target_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    
    kill_picture_url = Column(String(255), nullable=False)
    validation_picture = Column(String(255), nullable=True)
    assassin_gps = Column(String(255), nullable=True)
    target_gps = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    confirmed = Column(Boolean, default=False)
    
    def __init__(self, assassin_id, game_id, target_id, kill_picture_url, validation_picture=None, assassin_gps=None, target_gps=None):
        self.assassin_id = assassin_id
        self.game_id = game_id
        self.target_id = target_id
        self.kill_picture_url = kill_picture_url
        self.validation_picture = validation_picture
        self.assassin_gps = assassin_gps
        self.target_gps = target_gps

    def __repr__(self):
        return '<UserGame %d @ %d>' % (self.game_id, self.user_id)

    def get_api_response_dict(self):
        target = get_user(user_id=self.target_id)
        response_dict = {'assassin_username':target.username, \
                'shot_picture':self.kill_picture_url, \
                'victim_username':target.username, \
                'time': self.timestamp.strftime("%Y-%m-%d %H:%M:%S"), \
                }
        if self.assassin_gps is not None:
            response_dict['location'] = self.assassin_gps
        if self.completed_timestamp is not None:
            response_dict['completed'] = self.completed_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        return response_dict


class Shot(Base):
    __tablename__ = 'shot'
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    
    game_id = Column(Integer, ForeignKey('game.id'), primary_key=True)
    assassin_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    target_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    
    kill_id = Column(Integer, ForeignKey('kill.id'), nullable=True)
    shot_picture_url = Column(String(255), nullable=False)
    assassin_gps = Column(String(255), nullable=True)
    
    timestamp = Column(DateTime, default=datetime.datetime.now())
    valid = Column(Boolean, default=False)#we'll need to ignore invalid shots when calculating shot rate
    
    def __init__(self, assassin_id, target_id, game_id, shot_picture, assassin_gps=None, timestamp=datetime.datetime.now()):
        self.assassin_id = assassin_id
        self.target_id = target_id
        self.game_id = game_id
        self.shot_picture_url = shot_picture
        self.assassin_gps = assassin_gps
        self.timestamp = timestamp
        
    #A shot is valid if the following conditions are met:
    # 0: both players are alive
    # 1: the assassin had a mission targeting the target
    # 2: the assassin has remaining shots for the day
    # 3: the assassin does not need to wait for another shot
    
    def is_valid(self):
        
        try:
            #Step 0:  are both players alive?
            target_usergame = get_usergame(user_id=self.target_id, game_id=self.game_id)
            assassin_usergame = get_usergame(user_id=self.assassin_id, game_id=self.game_id)
            if not target_usergame.alive or not assassin_usergame.alive:
                return False
            
            #Step 1:  is the assassin targeting this person?
            mission = get_mission(assassin_id=self.assassin_id, target_id=self.target_id, game_id=self.game_id)
            
            #Step 2:  does the assassin have shots remaining?
            shots = get_shots_since(timestamp=datetime.datetime.today() - datetime.timedelta(hours=24), user_id=self.assassin_id, game_id=self.game_id, valid_only=True)
            if len(shots) >= assassin_usergame.max_shots_per_24_hours:
                return False
            
            #Step 3: If they have shots remaining, do they need to wait?
            if len(shots) != 0:
                most_recent_shot = shots[0] #their most recent shot
                if most_recent_shot is self:
                    if len(shots) > 1:
                        most_recent_shot = shots[1]
                    else:
                        return True
                
                minimum_timedelta_between_shots = datetime.timedelta(minutes=assassin_usergame.max_shot_interval_minutes)
                time_between_last_shot_and_this_one = self.timestamp - most_recent_shot.timestamp  
                if time_between_last_shot_and_this_one < minimum_timedelta_between_shots:
                    return False
            
            self.valid = True
            return True
        except Exception as e:
            self.valid = False
            return False

    def set_kill_id(self, kill_id):
        self.kill_id = kill_id

def get_shots_since(timestamp, user_id, game_id, valid_only=False):
    shots = Session().query(Shot).filter_by(assassin_id=user_id, game_id=game_id, valid=True).all()
#    filter(timestamp >= timestamp)
    shots_to_return = []
    for shot in shots:
        if shot.timestamp >= timestamp:
            if valid_only and not shot.valid:
                continue
            shots_to_return.append(shot)
    
    return sorted(shots_to_return, key=lambda shot: shot.timestamp, reverse=True) #sorted most recent - oldest 

def get_mission(game_id, assassin_username=None, assassin_id=None, target_id=None, mission_id=None):
    if assassin_username is None and assassin_id is None:
        raise Exception("Must supply either an assassin_username or an assassin_id")
    
    query = Session().query(Mission).filter_by(game_id=game_id, completed_timestamp=None)
    
    if mission_id is not None:
        query = query.filter_by(id=mission_id)
    
    if assassin_username is not None:
        user = get_user(username=assassin_username)
        assassin_id = user.id
    
    query = query.filter_by(assassin_id=assassin_id)
    
    if target_id is not None:
        query = query.filter_by(target_id=target_id)
    try:
        return_mission = query.one()
        return return_mission
    except NoResultFound:
        raise Exception("No mission found")
    
def get_missions(game_id, assassin_username=None, assassin_id=None):
    if assassin_username is None and assassin_id is None:
        raise Exception("Must supply either an assassin_username or an assassin_id")
    
    query = Session().query(Mission).filter_by(game_id=game_id)
    
    if assassin_username is not None:
        user = get_user(username=assassin_username)
        assassin_id = user.id
        
    if assassin_id is not None:
        query = query.filter_by(id=assassin_id)
    
    return query.all()

def get_kills(game_id, assassin_username=None, assassin_id=None):
    query = Session().query(Kill).filter_by(game_id=game_id)
    
    if assassin_username is not None:
        user = get_user(username=assassin_username)
        assassin_id = user.id
        
    if assassin_id is not None:
        query = query.filter_by(id=assassin_id)
    
    return query.all()


def get_usergame(user_id, game_id):
        return Session().query(UserGame).filter_by(user_id=user_id, game_id=game_id).one()

def get_usergames(user_id=None, username=None):
        if user_id is None and username is None:
            raise Exception("Must supply user_id or username")
        
        if user_id is None and username is not None:
            user_id = get_user(username=username).id
        return Session().query(UserGame).filter_by(user_id=user_id).all()
        
def get_user(username=None, password=None, user_id=None):
    if username is None and user_id is None:
        return None
    
    query = Session().query(User)

    if username is not None:
        query = query.filter_by(username=username)
    
    if user_id is not None:
        query = query.filter_by(id=user_id)
    
    if password is not None:
        query = query.filter_by(password=password)
    
    return query.one()

def get_game(game_id, game_password=None):
    query = Session().query(Game).filter_by(game_id=game_id)

    if game_password is not None:
        query = query.filter_by(password=game_password)
    
    return query.one()

    
def login(username, password):
    logger = logging.getLogger('login')
    session = Session()
    try:
        user = session.query(User).filter_by(username=username, password=password).one()
    except Exception, e:
        logger.exception(e)
        user = None
    return user

def create_user(username, password, profile_picture_binary):
#    profile_picture_url = ""
    profile_picture_url = imgur.upload(file_body=profile_picture_binary)
    s = Session()
    user = s.query(User).filter_by(username=username).first()
    if user is not None:
        raise Exception("Account already exists")
    else: 
        user = User(password=password, username=username, profile_picture=profile_picture_url)
        s.add(user)
        s.commit()
        s.flush()

def clear_all():
    for table in reversed(Base.metadata.sorted_tables):
        engine.execute(table.delete())
        

Base.metadata.create_all(engine)


