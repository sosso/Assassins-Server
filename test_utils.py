from models import Session, clear_all, User
import unittest

class BaseTest(unittest.TestCase):
    
    def setUp(self):
        self.session = Session()
    
    def tearDown(self):
        self.session.rollback()
        Session.remove()
        clear_all()

def make_users(number_of_users):
    users = []
    for user_number in range(number_of_users):
        users.append(User(username='Hitman' + str(user_number), password='123456', profile_picture='hitman.png'))
    return users
