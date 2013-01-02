from dbutils import get_or_create
from game_constants import DEFAULT_STARTING_MONEY, MAX_SHOT_INTERVAL_MINUTES, \
    MAX_SHOTS_PER_24_HOURS, DOUBLE_SHOT_PRICE, FAST_RELOAD_PRICE, BODY_DOUBLE_PRICE, \
    MISSION_COMPLETE_PAY
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
# from passlib.hash import sha256_crypt

if bool(os.environ.get('TEST_RUN', False)):
    engine = create_engine('mysql://anthony:password@127.0.0.1:3306/test_assassins', echo=False, pool_recycle=3600)  # recycle connection every hour to prevent overnight disconnect)
    if bool(os.environ.get('ANTHONY_TABLET_RUN', False)):
        engine = create_engine('mysql://root:root@127.0.0.1:3306/test_assassins', echo=False, pool_recycle=3600)  # recycle connection every hour to prevent overnight disconnect)
    else:
        engine = create_engine('mysql://anthony:password@127.0.0.1:3306/test_assassins', echo=False, pool_recycle=3600)  # recycle connection every hour to prevent overnight disconnect)
elif bool(os.environ.get('TEST_RUN_MIKE', False)):
    engine = create_engine('mysql://anthony@127.0.0.1:3306/test_assassins', echo=False, pool_recycle=3600)  # recycle connection every hour to prevent overnight disconnect)
else:
    engine = create_engine('mysql://b7cf3773be7303:3e0da60e@us-cdbr-east-02.cleardb.com/heroku_68620991f6061a0', echo=False, pool_recycle=3600)  # recycle connection every hour to prevent overnight disconnect)

Base = declarative_base(bind=engine)
sm = sessionmaker(bind=engine, autoflush=True, autocommit=False, expire_on_commit=False)
Session = scoped_session(sm)
logging.basicConfig()

class User(Base):
    __tablename__ = 'user'
    logger = logging.getLogger('User')
    # column definitions
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
    
    # None until it's associated with a kill
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

class InvalidGameRosterException(Exception): 
    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = message

class PowerupException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = message

class Game(Base):
    __tablename__ = 'game'
    # column definitions
    logger = logging.getLogger('Game')
    id = Column(INTEGER(), primary_key=True)
    title = Column(VARCHAR(length=255))
    password = Column(VARCHAR(length=255))
    starting_money = Column(Integer())
    max_shot_interval_minutes = Column(Integer(), default=MAX_SHOT_INTERVAL_MINUTES)
    max_shots_per_24_hours = Column(Integer(), default=MAX_SHOTS_PER_24_HOURS)
    started = Column(Boolean(), default=False)
    over = Column(Boolean(), default=False)
    
    # Powerup Enabled Columns
    body_double = Column(Boolean(), default=True)
    fast_reload = Column(Boolean(), default=True)
    double_shot = Column(Boolean(), default=True)
    
    def start(self):
        if len(self.get_players()) > 1 and len(self.game_masters) > 0:
            self.started = True
            self.assign_initial_missions()
        else:
            raise InvalidGameRosterException("Must have two or more players and 1 game master")
    
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
        usergame = get_or_create(s, UserGame, user_id=user.id, game_id=self.id, is_game_master=is_game_master, max_shots_per_24_hours=self.max_shots_per_24_hours, max_shot_interval_minutes=self.max_shot_interval_minutes)
        s.commit()

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
        s.commit()
    
    def mission_completed(self, mission, shot=None):
        # validate the mission belongs to this game
        if mission.game_id == self.id:
            pass
            # Get the target's mission to reassign it to the assassin
            targets_mission = object_session(self).query(Mission).filter_by(game_id=self.id, assassin_id=mission.target_id, completed_timestamp=None).one()
            mission.completed_timestamp = datetime.datetime.now()
            # Mark the target as dead
            if shot is not None:
                kill = Kill(game_id=mission.game_id, assassin_id=mission.assassin_id, target_id=mission.target_id,
                        kill_picture_url=shot.shot_picture_url)
            else:
                kill = Kill(game_id=mission.game_id, assassin_id=mission.assassin_id, target_id=mission.target_id,
                        kill_picture_url='')
            
            s = object_session(self)
            s.add(kill)
            s.flush()
            s.commit()
            
            target_usergame = get_usergame(mission.target_id, mission.game_id)
            target_usergame.alive = False
            s.add(target_usergame)
            s.flush()
            s.commit()
            if targets_mission.target_id == mission.assassin_id:  # meaning the players in question were targeting each other, and that the game should probably be over
                self.game_over()
            else:
                # Increase money of assassin for successfully completing mission
                s = object_session(self)
                assassin_usergame = s.query(UserGame).filter_by(user_id=mission.assassin_id, game_id=mission.game_id).one()
                assassin_usergame.money = assassin_usergame.money + MISSION_COMPLETE_PAY
                s.flush()
                s.commit()
                self.reassign_mission(new_assassin_id=mission.assassin_id, mission_to_reassign=targets_mission)
        else:
            raise Exception("Supplied mission does not belong to this game!")
    
    # TODO stub
    def game_over(self):
        s = object_session(self)
        self.over = True
        s.add(self)
        s.flush()
        s.commit()
        
    def reassign_mission(self, new_assassin_id, mission_to_reassign):
        # create a new mission with the proper assassin and target
        reassigned_mission = Mission(assassin_id=new_assassin_id, target_id=mission_to_reassign.target_id, game_id=self.id)
        session = object_session(self)
        try:
            session.add(reassigned_mission)
            session.flush()
            session.commit()
        except Exception, e:
            session.rollback()
            self.logger.exception(e)
            
    def disable_powerup(self, game_master_id, *enabled_powerup_ids):
        s = Session()
        game = s.query(Game).filter_by(id=self.id)
        dbl_shot_id = s.query(Powerup).filter_by(title='double_shot').value('id')
        fast_reload_id = s.query(Powerup).filter_by(title='fast_reload').value('id')
        body_double_id = s.query(Powerup).filter_by(title='body_double').value('id')
        
        for gm in self.game_masters:
            if(gm.id == game_master_id):
                for p in enabled_powerup_ids:
                    if(long(p) == body_double_id):
                        self.body_double = False
                    elif(long(p) == fast_reload_id):
                        self.fast_reload = False
                    elif(long(p) == dbl_shot_id):
                        self.double_shot = False
        s.flush()
        s.commit()
        
    def list_enabled_powerups(self):
        return list_enabled_powerups(self.id)
            

class UserGame(Base):
    __tablename__ = 'user_game'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    game_id = Column(Integer, ForeignKey('game.id'), primary_key=True)
    money = Column(Integer, nullable=False)
    alive = Column(Boolean)
    is_game_master = Column(Boolean, default=False, nullable=True)
    max_shot_interval_minutes = Column(Integer(), default=90)
    max_shots_per_24_hours = Column(Integer(), default=3)
    
    # User has powerups
    has_double_shot = Column(Boolean(), default=False)
    has_fast_reload = Column(Boolean(), default=False)
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
                'alive':self.alive, \
                'is_game_master':self.is_game_master, \
                'alive':self.alive, \
                'started':self.game.started, \
                'completed':self.game.over}
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
        try:
            if self.completed_timestamp is not None:
                response_dict['completed'] = self.completed_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except: pass
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
    valid = Column(Boolean, default=False)  # we'll need to ignore invalid shots when calculating shot rate
    
    def __init__(self, assassin_id, target_id, game_id, shot_picture, assassin_gps=None, timestamp=datetime.datetime.now()):
        self.assassin_id = assassin_id
        self.target_id = target_id
        self.game_id = game_id
        self.shot_picture_url = shot_picture
        self.assassin_gps = assassin_gps
        self.timestamp = timestamp
        
    # A shot is valid if the following conditions are met:
    # 0: both players are alive
    # 1: the assassin had a mission targeting the target
    # 2: the assassin has remaining shots for the day
    # 3: the assassin does not need to wait for another shot
    # 4: the target does not have a body double
    
    def is_valid(self):
        
        try:
            # Step 0:  are both players alive?
            target_usergame = get_usergame(user_id=self.target_id, game_id=self.game_id)
            assassin_usergame = get_usergame(user_id=self.assassin_id, game_id=self.game_id)
            if not target_usergame.alive or not assassin_usergame.alive:
                return False
            
            # Step 1:  is the assassin targeting this person?
            mission = get_mission(assassin_id=self.assassin_id, target_id=self.target_id, game_id=self.game_id)
            
            # Step 2:  does the assassin have shots remaining?
            shots = get_shots_since(timestamp=datetime.datetime.today() - datetime.timedelta(hours=24), user_id=self.assassin_id, game_id=self.game_id, valid_only=True)
            if len(shots) >= assassin_usergame.max_shots_per_24_hours:
                return False
            
            # Step 3: If they have shots remaining, do they need to wait?
            if len(shots) != 0:
                most_recent_shot = shots[0]  # their most recent shot
                if most_recent_shot is self:
                    if len(shots) > 1:
                        most_recent_shot = shots[1]
                    else:
                        return True
                
                minimum_timedelta_between_shots = datetime.timedelta(minutes=assassin_usergame.max_shot_interval_minutes)
                time_between_last_shot_and_this_one = self.timestamp - most_recent_shot.timestamp  
                if time_between_last_shot_and_this_one < minimum_timedelta_between_shots:
                    return False
            
            # Step 4: Does the target have a body double?
            if target_usergame.has_body_double:
                remove_body_double(target_usergame.user_id, target_usergame.game_id)
                return False
            
            self.valid = True
            return True
        except Exception as e:
            self.valid = False
            return False

    def set_kill_id(self, kill_id):
        self.kill_id = kill_id

class Powerup(Base):
    __tablename__ = 'powerup'
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    
    title = Column(VARCHAR(length=255))
    cost = Column(INTEGER())
    description = Column(VARCHAR(length=255))
    
    def __init__(self, title, cost, description):
        self.title = title
        self.cost = cost
        self.description = description
        
    def add_user_powerup(self, user, game, powerup):
        s = Session()
        ug = s.query(UserGame).filter_by(user_id=user.id, game_id=game.id).one()
        
        if(powerup.title == 'double_shot'):
            ug.has_double_shot = True
        elif(powerup.title == 'fast_reload'):
            ug.has_fast_reload = True
        elif(powerup.title == 'body_double'):
            ug.has_body_double = True
            
        s.flush()

    def get_api_response_dict(self):
        response_dict = {'powerup_id':self.id, \
                'powerup_name':self.title, \
                'powerup_cost':self.cost, \
                'powerup_description':self.description }
        return response_dict

def get_shots_since(timestamp, user_id, game_id, valid_only=False):
    shots = Session().query(Shot).filter_by(assassin_id=user_id, game_id=game_id, valid=True).all()
#    filter(timestamp >= timestamp)
    shots_to_return = []
    for shot in shots:
        if shot.timestamp >= timestamp:
            if valid_only and not shot.valid:
                continue
            shots_to_return.append(shot)
    
    return sorted(shots_to_return, key=lambda shot: shot.timestamp, reverse=True)  # sorted most recent - oldest 

def get_mission(game_id, assassin_username=None, assassin_id=None, target_id=None, mission_id=None, completed_timestamp=None):
    if assassin_username is None and assassin_id is None:
        raise Exception("Must supply either an assassin_username or an assassin_id")
    logger = logging.getLogger('get_mission')
    query = Session().query(Mission).filter_by(game_id=game_id, completed_timestamp=completed_timestamp)
    logger.info('mission fetch: gameid: %s assassin_username: %s assassin_id: %s target_id:%s mission_id: %s' % (str(game_id), str(assassin_username), str(assassin_id), str(target_id), str(mission_id)))
    if mission_id is not None:
        query = query.filter_by(id=mission_id)
    
    if assassin_username is not None:
        user = get_user(username=assassin_username)
        logger.info('via username, assassin_id is %s' % str(user.id))
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
    query = Session().query(Game).filter_by(id=game_id)

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
        
def get_powerup(powerup_title=None, powerup_id=None):
    if powerup_title is None and powerup_id is None:
        return None
    
    query = Session().query(Powerup)
    
    if powerup_title is not None:
        query = query.filter_by(title=powerup_title)
        
    if powerup_id is not None:
        query = query.filter_by(id=powerup_id)
        
    try:
        return query.one()
    except Exception, e:
        if powerup_title is not None:
            raise PowerupException("Powerup " + powerup_title + " does not exist")
        elif powerup_id is not None:
            raise PowerupException("Powerup " + powerup_id + " does not exist")
        else:
            raise e
        
def list_powerups():
    s = Session()
    
    powerups = s.query(Powerup).all()
        
    return powerups

def list_powerup_for_usergame(user, game_id):
    s = Session()
    
    usergame = s.query(UserGame).filter_by(user_id=user.id, game_id=game_id).one()
    powerups = list_powerups()
    powerups = sorted(powerups, key=lambda powerup: powerup.id)  # sorted smallest to largest id
    
    user_powerups_enabled = []
    
    if(usergame.has_body_double == True):
        user_powerups_enabled.append(powerups[2])
    if(usergame.has_fast_reload == True):
        user_powerups_enabled.append(powerups[1])
    if(usergame.has_double_shot == True):
        user_powerups_enabled.append(powerups[0])
        
    return sorted(user_powerups_enabled, key=lambda powerup: powerup.id)

def list_enabled_powerups(game_id):
    session = Session()
    enabled_list = []
    powerups = list_powerups()
    
    en = session.query(Game).filter_by(id=game_id).one()
    if(en.body_double == True):
        enabled_list.append(powerups[0])
    if(en.fast_reload == True):
        enabled_list.append(powerups[1])
    if(en.double_shot == True):
        enabled_list.append(powerups[2])
        
    return enabled_list
        
def purchase_powerup(user_id, game_id, powerup_id):
    s = Session()
    
    usergame = get_usergame(user_id, game_id)
    powerup = s.query(Powerup).filter_by(id=powerup_id).one()
    
    # Things to stop you from purchasing
    if(usergame.alive != True):
        raise PowerupException("You are dead.")
    if(usergame.money == 0):
        raise PowerupException("You have no money.")
    if(usergame.has_body_double == True and powerup.title == 'body_double'):
        raise PowerupException("You have already purchased a body double.")
    if(usergame.has_fast_reload == True and powerup.title == 'fast_reload'):
        raise PowerupException("You have already purchased fast reload")
    if(usergame.has_double_shot == True and powerup.title == 'double_shot'):
        raise PowerupException("You have already purchased double shot")
    
    if(usergame.money >= powerup.cost):
        usergame.money = usergame.money - powerup.cost
        _activate(user_id, game_id, powerup)
    else:
        raise PowerupException("You do not have enough money for that powerup")
    
    s.flush()
    
def _activate(user_id, game_id, powerup):
    s = Session()
    
    usergame = s.query(UserGame).filter_by(user_id=user_id, game_id=game_id).one()
    
    if(powerup.title == 'body_double'):
        usergame.has_body_double = True
    elif(powerup.title == 'fast_reload'):
        usergame.has_fast_reload = True
        usergame.max_shot_interval_minutes /= 2
    elif(powerup.title == 'double_shot'):
        usergame.has_double_shot = True
        usergame.max_shots_per_24_hours *= 2
    s.flush()
    
def populate_powerups():
    session = Session()
    
    dbl_shot_pwr = get_or_create(session, Powerup, title='double_shot', cost=DOUBLE_SHOT_PRICE, description="Double the number of shots you can fire in 24 hours")
    reload_pwr = get_or_create(session, Powerup, title='fast_reload', cost=FAST_RELOAD_PRICE, description="Half the time it takes to fire again")
    bdy_dbl_pwr = get_or_create(session, Powerup, title='body_double', cost=BODY_DOUBLE_PRICE, description="Have a body double take a shot meant for you")
    session.commit()

def remove_body_double(user_id, game_id):
    session = Session()
    ug = session.query(UserGame).filter_by(user_id=user_id, game_id=game_id).one()
    ug.has_body_double = False
    session.flush()
    session.commit()

Base.metadata.create_all(engine)


