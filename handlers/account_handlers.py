from handlers.response_utils import get_response_dict
from models import Session, login, create_user
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
