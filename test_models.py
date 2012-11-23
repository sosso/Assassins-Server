from models import User, Game, Session, engine, Base, login, clear_all
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker
import dbutils
import unittest

class BaseTest(unittest.TestCase):
    
    def setUp(self):
        self.session = Session()
    
    def tearDown(self):
        self.session.rollback()
        Session.remove()
        clear_all()
        
class TestUser(BaseTest):
    
    def test_user_creation(self):
        u = User(username='Hitman', password='123456', profile_picture='hitman.png')
        self.session.add(u)
        self.session.flush()
        self.assertEqual(1, len(self.session.query(User).filter_by(username='Hitman').all()))
    
    def test_login(self):
        user = User(username='login_test_hitman', password='login_test_password', profile_picture='hitman.png')
        self.session.add(user)
        self.session.flush()
        self.assertTrue(user is login(username=user.username, password=user.password))

class TestGame(BaseTest):
    
    def test_game_creation(self):
        users_list = make_users(4)
        self.session.add_all(users_list)
        game = Game(title='test game', password='testpassword', starting_money=3)
        self.session.add(game)
        self.session.flush()
        games_from_db = self.session.query(Game).all()
        self.assertEqual(1, len(games_from_db))
        self.assertEqual(game, games_from_db[0])
        
        
def make_users(number_of_users):
    users = []
    for user_number in range(number_of_users):
        users.append(User(username='Hitman'+str(user_number), password='123456', profile_picture='hitman.png'))
    return users

if __name__ == '__main__':
    clear_all()
    unittest.main()
    clear_all()
