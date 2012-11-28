from models import User, Game, Session, engine, Base, login, clear_all, Kill, \
    Mission, Shot
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker
from test_utils import BaseTest, make_users, make_game
import datetime
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
    
    """
    Create a game with a game master
    """
    def test_game_creation(self):
        game_master = make_users(1)[0]
        self.session.add(game_master)
        self.session.flush()
        game = Game(title='test game', password='testpassword', starting_money=3, game_master_id=game_master.id)
        self.session.add(game)
        games_from_db = self.session.query(Game).all()
        self.assertEqual(1, len(games_from_db))
        self.assertEqual(game, games_from_db[0]) 
    
    def test_game_start(self):
        game = make_game(self.session)
        assertFalse(game.started)
        
        #There's only one user, so the game can't start
        game.start()
        assertFalse(game.started)
        
        #Add a user, and the game still can't start because gamemasters can't play
        users = make_users(2)
        self.session.add_all(users)
        game.add_user(users[0])
        game.start()
        assertFalse(game.started)
        
        #Add the second player, and now we can start because we have two non-gamemaster players
        game.add_user(users[1])
        game.start()
        assertTrue(game.started)
        
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
    
class TestMission(BaseTest):
    
    def test_mission_creation(self):
        game = Game(title='test game', password='testpassword', starting_money=3)
        players = make_users(2)
        self.session.add(game)
        self.session.add_all(players)
        self.session.flush()
        
        mission = Mission(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id)
                      
        self.session.add(mission)
        missions_from_db = self.session.query(Mission).all()
        self.assertEqual(1, len(missions_from_db))
        self.assertEqual(mission, missions_from_db[0])

class TestShot(BaseTest):
    def test_shot_creation(self):
        game = Game(title='test game', password='testpassword', starting_money=3)
        players = make_users(2)
        self.session.add(game)
        self.session.add_all(players)
        self.session.flush()
        
        shot_picture = 'http://i.imgur.com/sSm81.jpg'
        
        shot = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W")
                      
        self.session.add(shot)
        shots_from_db = self.session.query(Shot).all()
        self.assertEqual(1, len(shots_from_db))
        self.assertEqual(shot, shots_from_db[0])
        
    def test_shot_frequency(self):
        game = make_game()
        players = make_users(2)
        self.session.add_all(players)
        self.session.flush()
        game.add_users(players)
        game.start()
        
        shot_picture = 'http://i.imgur.com/sSm81.jpg'
        
        self.assertEqual(3, players[0].get_shots_remaining(game.id))#user should have 3 shots since none have been fired
        
        #fire a shot
        valid_shot = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W")
        self.assertTrue(valid_shot.is_valid())
        self.assertEqual(2, players[0].get_shots_remaining(game.id)) #make sure the user only has 2 shots left
        
        #wait 89 minutes, and fire another shot.  Shouldn't work because it hasn't been 90 minutes.
        invalid_shot = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W",
                      timestamp=datetime.timedelta(minutes=89))
        self.assertEqual(2, players[0].get_shots_remaining(game.id))#the shot wasn't valid, so it shouldn't have been subtracted
        self.assertFalse(invalid_shot.is_valid())
        
        #wait 90 minutes from the valid shot and fire again.  This should work.
        valid_shot2 = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W",
                      timestamp=datetime.timedelta(minutes=90))
        self.assertTrue(valid_shot2.is_valid())
        self.assertEqual(1, players[0].get_shots_remaining(game.id))
        
        #wait 90+89 minutes, and fire another shot.  Shouldn't work because it hasn't been 90 minutes from valid shot 2.
        invalid_shot = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W",
                      timestamp=datetime.timedelta(minutes=90+89))
        self.assertEqual(1, players[0].get_shots_remaining(game.id))#the shot wasn't valid, so it shouldn't have been subtracted
        self.assertFalse(invalid_shot.is_valid())
        
        #wait 90+90 minutes from the valid shot and fire again.  This should work and is their LAST shot for the day.
        valid_shot3 = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W",
                      timestamp=datetime.timedelta(minutes=90+90))
        self.assertTrue(valid_shot3.is_valid())
        self.assertEqual(0, players[0].get_shots_remaining(game.id))
        
        #wait 90+90+89 minutes, and fire another shot.  Shouldn't work because they've used their 3 shots for the day!
        invalid_shot = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W",
                      timestamp=datetime.timedelta(minutes=90+90+89))
        self.assertEqual(0, players[0].get_shots_remaining(game.id))#the shot wasn't valid, so it shouldn't have been subtracted
        self.assertFalse(invalid_shot.is_valid())
        
        #wait 90+90+90 minutes from the valid shot and fire again.  This should still not work because they've used 3 shots!
        valid_shot3 = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W",
                      timestamp=datetime.timedelta(minutes=90+90+90))
        self.assertFalse(valid_shot3.is_valid())
        self.assertEqual(0, players[0].get_shots_remaining(game.id))
        
        #wait 24 hours and fire another shot.  Should work because it has been 24 minutes from first valid shot.
        #They still haven't recovered from their other 2 shots, however, so they have no remaining shots.
        valid_shot4 = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W",
                      timestamp=datetime.timedelta(minutes=24*60))
        self.assertEqual(0, players[0].get_shots_remaining(game.id))#they should have only had 1 valid shot, and now it's 0
        self.assertFalse(valid_shot4.is_valid())
        

def suite():
    user_tests = unittest.TestLoader().loadTestsFromTestCase(TestUser)
    game_tests = unittest.TestLoader().loadTestsFromTestCase(TestGame)
    kill_tests = unittest.TestLoader().loadTestsFromTestCase(TestKill)
    mission_tests = unittest.TestLoader().loadTestsFromTestCase(TestMission)
    return unittest.TestSuite([user_tests, game_tests, kill_tests, mission_tests])
