from models import get_user, Session
import logging
import simplejson
import tornado.web
def get_response_dict(success_bool, error_reason=None):
    response_dict = {}
    if success_bool:
        response_dict['success'] = "success"
    else:
        response_dict['success'] = "error"
        response_dict['reason'] = error_reason
    return response_dict

class AuthenticationException(Exception):
        def __init__(self, message):
            Exception.__init__(self, message)
            self.message = message
    
class BaseHandler(tornado.web.RequestHandler):
    def _handle_request_exception(self, e):
        if isinstance(e, AuthenticationException):
            self.send_error_override(500, auth_err_json=simplejson.dumps(get_response_dict(False, e.message)))
        else:
            super(BaseHandler, self)._handle_request_exception(e)
    
    def send_error_override(self, status_code=500, **kwargs):
        if self._headers_written:
#            logging.error("Cannot send error response after headers written")
            if not self._finished:
                self.finish()
            return
        if 'auth_err_json' in kwargs:
            errjson = kwargs.pop('auth_err_json')
            self.clear()
            self.set_status(status_code)
            self.finish(errjson)
            
        else:
            super(BaseHandler, self).send_error(status_code, **kwargs)

def auth_required(http_method):
    def wrapper(self, *args, **kwargs):
        logger = logging.getLogger('Auth_required')
        logger.info('Auth request: %s' % self.get_argument('username', 'no username'))
        try:
            try: username = self.get_argument('username')
            except: 
                if self.get_argument('game_master_username', None) is None:
                    raise AuthenticationException("Must supply username")
                else:
                    username = self.get_argument('game_master_username')
            password = self.get_argument('password', None)
            secret_token = self.get_argument('secret_token', None)
            if password is None and secret_token is None:
                raise AuthenticationException("Must supply password and/or secret token")
            else:
                try: user = get_user(username=username)
                except Exception as e: 
                    self.session.rollback()
                    logger.exception(e)
                    raise AuthenticationException("Invalid username")
                if password is not None:                
                    if not user.valid_password(password):
                        raise AuthenticationException("Invalid password")
                elif secret_token is not None:
                    if not user.valid_password(secret_token):
                        raise AuthenticationException("Invalid secret_token")
        except Exception as e:
            self.session.rollback()
            logger.exception(e)
            raise    
        return http_method(self, *args, **kwargs)
    return wrapper
