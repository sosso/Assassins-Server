from models import Session, clear_all, User, Game
import unittest

class BaseTest(unittest.TestCase):
    
    def setUp(self):
        self.session = Session()
    
    def tearDown(self):
        self.session.rollback()
        Session.remove()
        clear_all()

class APIBaseTest(unittest.TestCase):
    
    def setUp(self):
        clear_all()
        
    def tearDown(self):
        clear_all()


def make_users(number_of_users, session=None):
    users = []
    for user_number in range(number_of_users):
        users.append(User(username='Hitman' + str(user_number), password='123456', profile_picture='hitman.png'))

    if session is not None:
        session.add_all(users)
        session.flush()    
    return users

def make_game(session):
    game = Game(title='test game', password='testpassword', starting_money=3)
#    game.add_game_master(user_id=game_master.id)
    session.add(game)
    session.flush()
    return game

def make_game_with_master(session, add_gm_to_game=True):
    game_master = make_users(1)[0]
    session.add(game_master)
    session.flush()
    game = Game(title='test game', password='testpassword', starting_money=3)
    session.add(game)
    session.flush()
    if add_gm_to_game:
        game.add_game_master(user_id=game_master.id)
    return (game_master, game)
