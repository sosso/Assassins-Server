from models import User, Item, ItemCompletion, Session, UserGame, get_user
from pkg_resources import StringIO
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.functions import random
import dbutils
import os
import simplejson
import tornado

#logger = logging.getLogger('modelhandlers')

"""
username
item_id
<file>
"""
class LoginHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        session = Session()
        try:
            user = get_user(username=username, password=password)
            final_string = "SUCCESS"
        except NoResultFound:
            
        except Exception:
            session.rollback()
            final_string = "ERROR"
        finally:
            Session.remove()
            self.finish(simplejson.dumps({'result':final_string}))


class CreateUserHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')
        picture = self.get_argument('profile_picture')

        session = Session()
        try:
            user = get_user(username=username, password=password)
            user = dbutils.get_or_create(session, User, username=username)
            final_string = "User creation successful!"
        except Exception, e:
            session.rollback()
            final_string = "User creation failed."
        finally:
            Session.remove()
            self.finish(final_string)
