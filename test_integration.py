from models import Game
from test_utils import BaseTest, make_users
import unittest


class TestUserGame(BaseTest):
    
    def test_add_users_to_game(self):
        users_list = make_users(4)
        self.session.add_all(users_list)
        game = Game(title='test game', password='testpassword', starting_money=3)
        self.session.add(game)
        self.session.flush()
        game.add_users(users_list)
        
        game_from_db = self.session.query(Game).filter_by(title=game.title).one()
        self.assertEqual(users_list, game_from_db.user_list)
        
def suite():
    user_game_tests = unittest.TestLoader().loadTestsFromTestCase(TestUserGame)
    return unittest.TestSuite([user_game_tests])
