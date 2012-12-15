from handlers.response_utils import auth_required, get_response_dict
from models import Session, get_user, purchase_powerup, list_enabled_powerups, \
    list_powerup_for_usergame, get_game, get_usergame
import logging
import simplejson
import tornado.web

#logger = logging.getLogger('modelhandlers')

# Purchase and activate a powerup
class BuyPowerup(tornado.web.RequestHandler):
    @auth_required
    @tornado.web.asynchronous
    def post(self):
        logger = logging.getLogger("BuyPowerup")
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

# List purchased powerups
class Inventory(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @auth_required
    def get(self):
        logger = logging.getLogger('Inventory')
        username = self.get_argument('username')
        game_id = self.get_argument('game_id')      
       
        try:
            session = Session()
         
            user = get_user(username)
            pwrlist = list_powerup_for_usergame(user, game_id)
            purchased_json_array = []
            for powerup in pwrlist:
                purchased_json_array.append(powerup.get_api_response_dict())
            return_obj = purchased_json_array
            
        except Exception, e:
            logger.exception(e)
            session.rollback()
            return_obj = []
        finally:
            Session.remove()
            self.finish(simplejson.dumps(return_obj))

# List available powerups for purchase
class ViewAvailable(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @auth_required
    def get(self):
        logger = logging.getLogger('ViewAvailablePowerups')
        try:
            game_id = self.get_argument('game_id')
            session = Session()
            powerup_json_array = []
            powerups_from_db = list_enabled_powerups(game_id)
            for powerup in powerups_from_db:
                powerup_json_array.append(powerup.get_api_response_dict())
            return_obj = powerup_json_array
        except Exception, e:
            logger.exception(e)
            session.rollback()
            return_obj = []
        finally:
            Session.remove()
            self.finish(simplejson.dumps(return_obj))

# Game Master can disable powerups for a game
class DisablePowerup(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @auth_required
    def post(self):
        logger = logging.getLogger('DisablePowerup')
        session = Session()
        try:
            game_id = self.get_argument('game_id')
            username = self.get_argument('username')
            power_id = self.get_argument('powerup_id')
            user = get_user(username)
            ug = get_usergame(user.id, game_id)
            
            if(ug.is_game_master):
                game = get_game(game_id)
                game.disable_powerup(user.id, power_id)
                session.commit()
                result_dict = get_response_dict(True)
            else:
                raise Exception("You are not a Game Master for the given game_id")
            
        except Exception, e:
            logger.exception(e)
            session.rollback()
            result_dict = get_response_dict(False, e.message)
        finally:
            Session.remove()
            self.finish(simplejson.dumps(result_dict))
                