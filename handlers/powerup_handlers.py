from handlers.response_utils import auth_required
from models import Session
import simplejson
import tornado.web

#logger = logging.getLogger('modelhandlers')

class BuyPowerup(tornado.web.RequestHandler):
    @auth_required
    @tornado.web.asynchronous
    def get(self):
        username = self.get_argument('username')
        item_id = self.get_argument('item_id')

        session = Session()
        try:
            pass
        except Exception, e:
            session.rollback()
            final_string = "Oops!  Something went wrong.  Please try again"
        finally:
            Session.remove()
            self.finish(final_string)


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

class ViewEnabled(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @auth_required
    def get(self):
        item_id = self.get_argument('itemid')
        description = self.get_argument('description', '')

        session = Session()
        try:
            finish_string = "Item added"
        except Exception, e:
            session.rollback()
            finish_string = "Item not added"
        finally:
            Session.remove()
            self.finish(finish_string)


