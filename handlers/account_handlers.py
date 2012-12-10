from handlers.response_utils import get_response_dict, auth_required, \
    BaseHandler
from models import Session, login, create_user
import logging
import simplejson
import tornado.web


class LoginHandler(BaseHandler):
    @auth_required
    @tornado.web.asynchronous
    def post(self):
        try:
            result_dict = get_response_dict(True)
        except Exception as e:
            self.session.rollback()
            result_dict = get_response_dict(False, e.message)
        finally:
            self.finish(simplejson.dumps(result_dict))

class CreateUserHandler(tornado.web.RequestHandler):
    def post(self):
        logger = logging.getLogger('CreateUserHandler')
        username = self.get_argument('username')
        password = self.get_argument('password')
        logger.info('Create user request received, args grabbed')
        session = Session()
        result_dict = {}
        try:
            picture_binary = self.request.files['profile_picture'][0]['body']    
            create_user(username=username, password=password, profile_picture_binary=picture_binary)
            result_dict = get_response_dict(True)
            result_dict['username'] = username
        except Exception, e:
            logger.exception(e)
            session.rollback()
            result_dict = get_response_dict(False, e.message)
        finally:
            Session.remove()
            self.finish(simplejson.dumps(result_dict))
