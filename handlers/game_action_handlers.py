from handlers.response_utils import get_response_dict
from models import User, Session, UserGame, get_user, Game, get_mission
import dbutils
import game_constants
import simplejson
import tornado

#logger = logging.getLogger('modelhandlers')

class CreateGame(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self):
        friendly_name = self.get_argument('friendly_name')
        game_master_username = self.get_argument('game_master_username')
        base_money = int(self.get_argument('base_money'), game_constants.DEFAULT_STARTING_MONEY)
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
            result_dict = get_response_dict(False, e.msg)
        finally:
            Session.remove()
            self.finish(simplejson.dumps(result_dict))


class ViewMission(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        username = self.get_argument('username')
        game_id = self.get_argument('game_id')
        mission_id = self.get_argument('mission_id')
        session = Session()
        try:
            mission = get_mission(assassin_username=username, game_id=game_id, mission_id=mission_id)
            return_dict = mission.get_api_response_dict()
        except Exception as e:
            return_dict = get_response_dict(False, e.msg)
            session.rollback()
        finally:
            Session.remove()
            self.finish(simplejson.dumps(return_dict))

class ViewAllMissions(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        username = self.get_argument('username')
        game_id = self.get_argument('game_id')
        session = Session()
        try:
            user = dbutils.get_or_create(session, User, username=username)
            final_string = "User creation successful!"
        except Exception, e:
            session.rollback()
            final_string = "User creation failed."
        finally:
            Session.remove()
            self.finish(final_string)

class Assassinate(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        username = self.get_argument('username')
        game_id = self.get_argument('game_id')
        shot_picture = None
        target_username = self.get_argument('target_username')
        mission_id = self.get_argument('mission_id', None)
        session = Session()
        try:
            finish_string = "Item added"
#            completed_items = session.Query(ItemCompletion).filter()
        except Exception, e:
            session.rollback()
            finish_string = "Item not added"
        finally:
            Session.remove()
            self.finish(finish_string)

class DisputeHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        item_id = self.get_argument('itemid')
        description = self.get_argument('description', '')

        session = Session()
        try:
            item = dbutils.get_or_create(session, Item, item_id=item_id)
            item.description = description
            session.add(item)
            session.flush()
            session.commit()
            finish_string = "Item added"
#            completed_items = session.Query(ItemCompletion).filter()
        except Exception, e:
            session.rollback()
            finish_string = "Item not added"
        finally:
            Session.remove()
            self.finish(finish_string)

class ViewKills(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        item_id = self.get_argument('itemid')
        description = self.get_argument('description', '')

        session = Session()
        try:
            item = dbutils.get_or_create(session, Item, item_id=item_id)
            item.description = description
            session.add(item)
            session.flush()
            session.commit()
            finish_string = "Item added"
#            completed_items = session.Query(ItemCompletion).filter()
        except Exception, e:
            session.rollback()
            finish_string = "Item not added"
        finally:
            Session.remove()
            self.finish(finish_string)

class JoinGame(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        item_id = self.get_argument('itemid')
        description = self.get_argument('description', '')

        session = Session()
        try:
            item = dbutils.get_or_create(session, Item, item_id=item_id)
            item.description = description
            session.add(item)
            session.flush()
            session.commit()
            finish_string = "Item added"
#            completed_items = session.Query(ItemCompletion).filter()
        except Exception, e:
            session.rollback()
            finish_string = "Item not added"
        finally:
            Session.remove()
            self.finish(finish_string)
            
