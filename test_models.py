from models import User, Game, Session, engine, Base
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker
import unittest

class BaseTest(unittest.TestCase):
    def teardown(self):
        Session.remove()

class TestUser(BaseTest):
    
    def test_user_creation(self):
        session = Session()
        u = User(username='Hitman', password='123456', profile_picture='hitman.png')
        session.add(u)
        self.assertEqual(1, len(session.query(User).filter_by(username='Hitman').all()))

class TestGame(BaseTest):
    
    def test_game_creation(self):
        session = Session()
        users_list = make_users(4)
        session.add_all(users_list)
        game = Game(title='test game', password='testpassword', starting_money=3)
        session.add(game)
        games_from_db = session.query(Game).all()
        self.assertEqual(1, len(games_from_db))
        self.assertEqual(game, games_from_db[0])
        
        
def make_users(number_of_users):
    users = []
    for user_number in range(number_of_users):
        users.append(User(username='Hitman'+str(user_number), password='123456', profile_picture='hitman.png'))
    return users

if __name__ == '__main__':
    unittest.main()
    Base.metadata.drop_all()
    
