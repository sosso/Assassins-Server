from handlers.response_utils import get_response_dict, auth_required
from models import Session, get_user, Game, get_mission, get_missions, get_game, \
    get_kills, Shot, get_usergames
import game_constants
import imgur
import simplejson
import tornado.web

#logger = logging.getLogger('modelhandlers')

class CreateGame(tornado.web.RequestHandler):
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

class ViewMission(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @auth_required
    def get(self):
        username = self.get_argument('username')
        game_id = self.get_argument('game_id')
        mission_id = self.get_argument('mission_id', None)
        session = Session()
        try:
            mission = get_mission(assassin_username=username, game_id=game_id, mission_id=mission_id)
            return_dict = mission.get_api_response_dict()
        except Exception as e:
            return_dict = get_response_dict(False, e.message)
            session.rollback()
        finally:
            Session.remove()
            self.finish(simplejson.dumps(return_dict))

#TODO handle game master case
class ViewAllMissions(tornado.web.RequestHandler):
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

class Assassinate(tornado.web.RequestHandler):
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
            mission = get_mission(game_id=game_id, assassin_username=username, target_username=target_username)
            
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
                game.mission_completed(mission)
                response_dict = get_response_dict(True)
            else:
                response_dict = get_response_dict(False, "Shot invalid.  If this was your target in this game, maybe you need to wait?")
            
        except Exception as e:
            session.rollback()
            response_dict = get_response_dict(False, e.message)
        finally:
            Session.remove()
            self.finish(simplejson.dumps(response_dict))

#TODO
class DisputeHandler(tornado.web.RequestHandler):
    @auth_required
    @tornado.web.asynchronous
    def get(self):
        item_id = self.get_argument('itemid')
        description = self.get_argument('description', '')

        session = Session()
        try:
            pass
        except Exception, e:
            session.rollback()
            finish_string = "Item not added"
        finally:
            Session.remove()
            self.finish(finish_string)

class ViewKills(tornado.web.RequestHandler):
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

class GetListOfJoinedOrJoinGame(tornado.web.RequestHandler):
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
            game.add_user(user)
            response_dict = get_response_dict(True)
        except Exception as e:
            session.rollback()
            response_dict = get_response_dict(False, e.message)
        finally:
            Session.remove()
            self.finish(simplejson.dumps(response_dict))
            
