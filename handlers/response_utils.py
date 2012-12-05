from models import get_user
def get_response_dict(success_bool, error_reason=None):
    response_dict = {}
    if success_bool:
        response_dict['success'] = "success"
    else:
        response_dict['success'] = "error"
        response_dict['reason'] = error_reason
    return response_dict

class AuthenticationException(Exception):
        pass

def auth_required(request):
    def decorated_get(self):
        try: username = self.get_argument('username')
        except: raise AuthenticationException("Must supply username")
        password = self.get_argument('password', None)
        secret_token = self.get_argument('secret_token', None)
        if password is None and secret_token is None:
            raise AuthenticationException("Must supply password and/or secret token")
        else:
            try: user = get_user(username=username)
            except: raise AuthenticationException("Invalid username")
            if password is not None:                
                if not user.valid_password(password):
                    raise AuthenticationException("Invalid password")
            elif secret_token is not None:
                if not user.valid_password(secret_token):
                    raise AuthenticationException("Invalid secret_token")    
        print "User authenticated!"
        return
    return decorated_get
