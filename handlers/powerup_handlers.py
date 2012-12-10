from handlers.response_utils import auth_required, get_response_dict
from models import Session, get_user, purchase_powerup, list_enabled_powerups
import simplejson
import tornado.web
import logging

#logger = logging.getLogger('modelhandlers')

class BuyPowerupHandler(tornado.web.RequestHandler):
    @auth_required
    @tornado.web.asynchronous
    def post(self):
        logger = logging.getLogger("BuyPowerupHandler")
        session = Session()
        try:
            username = self.get_argument('username')
            item_id = self.get_argument('item_id')
            game_id = self.get_argument('game_id')
        
            user = get_user(username)
            purchase_powerup(user.id, game_id, item_id)
            session.commit()
            result_dict = get_response_dict(True)
        except Exception, e:
            logger.exception(e)
            session.rollback()
            result_dict = get_response_dict(False, e.message)
        finally:
            Session.remove()
            self.finish(simplejson.dumps(result_dict))


class ActivatePowerup(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @auth_required
    def get(self):
        username = self.get_argument('username')

        session = Session()
        try:
            pass
        except Exception, e:
            session.rollback()
        Session.remove()
        self.finish(simplejson.dumps())

class Inventory(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @auth_required
    def get(self):
        username = self.get_argument('username')
        session = Session()
        try:
            pass
            final_string = "User creation successful!"
        except Exception, e:
            session.rollback()
            final_string = "User creation failed."
        finally:
            Session.remove()
            self.finish(final_string)

class ViewAvailable(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @auth_required
    def get(self):
        try:
            game_id = self.get_argument('game_id')
            session = Session()
            powerup_json_array = []
            powerups_from_db = list_enabled_powerups(game_id)
            for powerup in powerups_from_db:
                powerup_json_array.append(powerup.get_api_response_dict())
            return_obj = powerup_json_array
        except Exception, e:
            session.rollback()
            return_obj = []
        finally:
            Session.remove()
            self.finish(simplejson.dumps(return_obj))


