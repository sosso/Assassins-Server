from models import User, Game, Session, engine, Base, login, clear_all, Kill
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker
from test_utils import BaseTest, make_users
import dbutils
import unittest
class TestUser(BaseTest):
    
    def test_user_creation(self):
        u = User(username='Hitman', password='123456', profile_picture='hitman.png')
        self.session.add(u)
        self.assertEqual(1, len(self.session.query(User).filter_by(username='Hitman').all()))
    
    def test_login(self):
        user = User(username='login_test_hitman', password='login_test_password', profile_picture='hitman.png')
        self.session.add(user)
        self.assertTrue(user is login(username=user.username, password=user.password))

class TestGame(BaseTest):
    
    def test_game_creation(self):
        game = Game(title='test game', password='testpassword', starting_money=3)
        self.session.add(game)
        games_from_db = self.session.query(Game).all()
        self.assertEqual(1, len(games_from_db))
        self.assertEqual(game, games_from_db[0]) 

class TestKill(BaseTest):
    
    def test_kill_creation(self):
        game = Game(title='test game', password='testpassword', starting_money=3)
        players = make_users(2)
        kill_picture = 'http://i.imgur.com/sSm81.jpg'
        self.session.add(game)
        self.session.add_all(players)
        self.session.flush()
        
        kill = Kill(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      kill_picture_url=kill_picture,
                      game_id=game.id)
                      
        self.session.add(kill)
        kills_from_db = self.session.query(Kill).all()
        self.assertEqual(1, len(kills_from_db))
        self.assertEqual(kill, kills_from_db[0]) 
    
if __name__ == '__main__':
    clear_all()
    unittest.main()
    clear_all()
