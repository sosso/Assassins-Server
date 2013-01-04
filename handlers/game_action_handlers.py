from handlers.response_utils import get_response_dict, auth_required, \
    BaseHandler
from models import Session, get_user, Game, get_mission, get_missions, get_game, \
    get_kills, Shot, get_usergames, get_usergame, get_kill, get_shot, Dispute
import game_constants
import imgur
import logging
import simplejson
import tornado.web

# logger = logging.getLogger('modelhandlers')

class CreateGame(BaseHandler):
    @tornado.web.asynchronous
    @auth_required
    def post(self):
        friendly_name = self.get_argument('friendly_name')
        game_master_username = self.get_argument('game_master_username')
        try:
            base_money = int(self.get_argument('base_money'))
        except:
            base_money = game_constants.DEFAULT_STARTING_MONEY
        password = self.get_argument('game_password')
        session = Session()
        try:
            game_master = get_user(game_master_username)
            game = Game(title=friendly_name, password=password, starting_money=base_money)
            session.add(game)
            session.flush()
            game.add_game_master(game_master)
            result_dict = get_response_dict(True)
            session.commit()
            result_dict['game_id'] = game.id
        except Exception as e:
            session.rollback()
            result_dict = get_response_dict(False, e.message)
        finally:
            Session.remove()
            self.finish(simplejson.dumps(result_dict))

class ViewMission(BaseHandler):
    @tornado.web.asynchronous
    @auth_required
    def get(self):
        username = self.get_argument('username')
        game_id = self.get_argument('game_id')
        mission_id = self.get_argument('mission_id', None)
        logger = logging.getLogger('ViewMission')
        session = Session()
        try:
            mission = get_mission(assassin_username=username, game_id=game_id, mission_id=mission_id)
            return_dict = mission.get_api_response_dict()
        except Exception as e:
            return_dict = get_response_dict(False, e.message)
            session.rollback()
        finally:
            Session.remove()
            logger.info('Mission returning %s' % str(simplejson.dumps(return_dict)))
            self.finish(simplejson.dumps(return_dict))

# TODO handle game master case
class ViewAllMissions(BaseHandler):
    @tornado.web.asynchronous
    @auth_required
    def get(self):
        username = self.get_argument('username')
        game_id = self.get_argument('game_id')
        session = Session()
        try:
            missions_json_array = []
            missions_from_db = get_missions(assassin_username=username, game_id=game_id)
            for mission in missions_from_db:
                missions_json_array.append(mission.get_api_response_dict())
            return_obj = missions_json_array
        except Exception as e:
            session.rollback()
            return_dict = []
        finally:
            Session.remove()
            self.finish(simplejson.dumps(return_dict))

class Assassinate(BaseHandler):
    @tornado.web.asynchronous
    @auth_required
    def post(self):
        username = self.get_argument('username')
        game_id = self.get_argument('game_id')
        shot_picture = None
        target_username = self.get_argument('target_username')
        mission_id = self.get_argument('mission_id', None)
        session = Session()
        try:
            target_user = get_user(username=target_username)
            assassin_user = get_user(username=username)
            game = get_game(game_id)
            mission = get_mission(game_id=game_id, assassin_username=username, target_id=target_user.id)
            
            picture_binary = self.request.files['shot_picture'][0]['body']
            shot_picture_url = imgur.upload(file_body=picture_binary)

            player_shooting_target = Shot(assassin_id=assassin_user.id, \
                                        target_id=target_user.id, \
                                        game_id=game_id, \
                                        shot_picture=shot_picture_url)
            session.add(player_shooting_target)
            session.flush()
            session.commit()
            if player_shooting_target.is_valid():
                target_usergame = get_usergame(user_id=target_user.id, game_id=game_id)
                target_usergame.alive = None  # mark them as shot
                session.add(target_usergame)
                session.flush()
                session.commit()
                response_dict = get_response_dict(True)
            else:
                response_dict = get_response_dict(False, "Shot invalid.  If this was your target in this game, maybe they had a body double or you need to wait?")
        except Exception as e:
            session.rollback()
            response_dict = get_response_dict(False, e.message)
        finally:
            Session.remove()
            self.finish(simplejson.dumps(response_dict))

class ShotHandler(BaseHandler):
    @auth_required
    @tornado.web.asynchronous
    def get(self):
        shot_id = self.get_argument('shot_id')
        session = Session()
        try:
            shot = get_shot(shot_id)
            response_dict = shot.get_api_response_dict()
        except Exception, e:
            session.rollback()
            response_dict = get_response_dict(False, e.message)
        finally:
            Session.remove()
            self.finish(simplejson.dumps(response_dict))
    
    @auth_required
    @tornado.web.asynchronous
    def post(self):
        shot_id = self.get_argument('shot_id')
        username = self.get_argument('username')
        shot_upheld = self.get_argument('shot_upheld')
        claim = self.get_argument('claim', '')
        
        resolving_user = get_user(username=username)
        shot = get_shot(shot_id)
        game = get_game(shot.game_id)
        session = Session()
        
        mission = get_mission(game_id=game.game_id, assassin_id=shot.assassin_id, target_id=shot.target_id, completed_timestamp=None)
        
        if bool(shot_upheld):
            if shot.target_id == resolving_user.id or resolving_user in game.game_masters:
                shot.kill_upheld = True
                game.mission_completed(mission)
                response_dict = get_response_dict(True)
        else:
            if shot.target_id == resolving_user.id:
                dispute = Dispute(game.game_id, shot_id, claim)
                session.add(dispute)
                session.flush()
                session.commit()
            elif resolving_user in game.game_masters:
                shot.kill_upheld = False
            

# TODO
class DisputeHandler(BaseHandler):
    @auth_required
    @tornado.web.asynchronous
    def post(self):
        username = self.get_argument('username')
        game_id = self.get_argument('game_id')
        shot_id = self.get_argument('shot_id')
        shot_upheld = self.get_argument('shot_upheld')

        session = Session()
        try:
            shot = session.query(Shot).filter_by(id=shot_id)
            resolving_user = get_user(username=username)
            game = get_game(game_id)
            mission = get_mission(game_id=game_id, assassin_id=shot.assassin_id, target_id=shot.target_id, completed_timestamp=None)
            if resolving_user in game.game_masters:
                if bool(shot_upheld):
                    game.mission_completed(mission)
                else:
                    pass
                response_dict = get_response_dict(True)
            else:
                response_dict = get_response_dict(False, 'Only the game master can resolve a dispute')
        except Exception, e:
            session.rollback()
            response_dict = get_response_dict(False, e.message)
        finally:
            Session.remove()
            self.finish(response_dict)

class ViewKills(BaseHandler):
    @auth_required
    @tornado.web.asynchronous
    def get(self):
        game_id = self.get_argument('game_id')

        session = Session()
        try:
            kills_json_array = []
            kills_from_db = get_kills(game_id=game_id)
            for kill in kills_from_db:
                kills_json_array.append(kill.get_api_response_dict())
            return_obj = kills_json_array
        except Exception as e:
            session.rollback()
            return_obj = []
        finally:
            Session.remove()
            self.finish(simplejson.dumps(return_obj))

class GetListOfJoinedOrJoinGame(BaseHandler):
    @auth_required
    @tornado.web.asynchronous
    def get(self):
        username = self.get_argument('username')
        session = Session()
        try:
            usergames_json_array = []
            usergames = get_usergames(username=username)
            for usergame in usergames:
                usergames_json_array.append(usergame.get_api_response_dict())
            response_obj = usergames_json_array
        except Exception as e:
            session.rollback()
            response_obj = []
        finally:
            Session.remove()
            self.finish(simplejson.dumps(response_obj))
    
    @auth_required
    @tornado.web.asynchronous
    def post(self):
        game_id = self.get_argument('game_id')
        game_password = self.get_argument('game_password')
        username = self.get_argument('username')

        session = Session()
        try:
            user = get_user(username)
            game = get_game(game_id=game_id, game_password=game_password)
            try:
                usergame = get_usergame(user.id, game.id)
                if usergame is not None:
                    response_dict = get_response_dict(True)
            except:
                game.add_user(user)
        except Exception as e:
            session.rollback()
            response_dict = get_response_dict(False, e.message)
        finally:
            Session.remove()
            self.finish(simplejson.dumps(response_dict))
            
