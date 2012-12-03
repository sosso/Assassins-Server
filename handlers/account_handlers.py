from models import User, Session, UserGame, get_user, \
    login, create_user
from pkg_resources import StringIO
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.functions import random
import dbutils
import os
import simplejson
import tornado
from handlers.response_utils import get_response_dict

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
            user = login(username=username, password=password)
            if user is not None:
                pass
                #TODO return their token
        except Exception as e:
            session.rollback()
            result_dict = get_response_dict(False, e.msg)
        finally:
            Session.remove()
            self.finish(simplejson.dumps(result_dict))


class CreateUserHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self):
        username = self.get_argument('username')
        password = self.get_argument('password')

        session = Session()
        result_dict = {}
        try:
            picture_binary = self.request.files['profile_picture'][0]['body']    
            create_user(username = username, password=password, profile_picture=picture_binary)
            result_dict = get_response_dict(True)
        except Exception, e:
            session.rollback()
            result_dict = get_response_dict(False, e.msg)
        finally:
            Session.remove()
            self.finish(simplejson.dumps(result_dict))
