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
        logger = logging.getLogger('LoginHandler')
        try:
            logger.info('Login request: %s %s' % (self.get_argument('username'), self.get_argument('password')))
            result_dict = get_response_dict(True)
        except Exception as e:
            logger.exception(e)
            Session().rollback()
            result_dict = get_response_dict(False, e.message)
        finally:
            logger.info('Login result_dict: %s' % str(result_dict))
            self.finish(simplejson.dumps(result_dict))

class CreateUserHandler(tornado.web.RequestHandler):
    def post(self):
        logger = logging.getLogger('CreateUserHandler')
        username = self.get_argument('username')
        password = self.get_argument('password')
        email = self.get_argument('email')
        logger.info('Create user request received, args grabbed')
        session = Session()
        result_dict = {}
        try:
            picture_binary = self.request.files['profile_picture'][0]['body']    
            create_user(username=username, password=password, profile_picture_binary=picture_binary, email=email)
            result_dict = get_response_dict(True)
            result_dict['username'] = username
        except Exception, e:
            logger.exception(e)
            session.rollback()
            result_dict = get_response_dict(False, e.message)
        finally:
            Session.remove()
            self.finish(simplejson.dumps(result_dict))
