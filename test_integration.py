from models import User, Game, Session, engine, Base, login, clear_all
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker
from test_utils import BaseTest, make_users
import dbutils
import unittest


class TestUserGame(BaseTest):
    
    def test_add_users_to_game(self):
        users_list = make_users(4)
        self.session.add_all(users_list)
        game = Game(title='test game', password='testpassword', starting_money=3)
        self.session.add(game)
        game.add_users(users_list)
        
        game_from_db = self.session.query(Game).filter_by(title=game.title).one()
        self.assertEqual(users_list, game_from_db.user_list)
        
        
if __name__ == '__main__':
    clear_all()
    unittest.main()
    clear_all()
