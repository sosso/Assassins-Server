from game_constants import MAX_SHOTS_PER_24_HOURS, MAX_SHOT_INTERVAL_MINUTES
from models import User, Game, login, Kill, Mission, Shot, \
    InvalidGameRosterException, Powerup, UserGame, purchase_powerup, \
    PowerupException, get_usergame
from test_utils import BaseTest, make_users, make_game, make_game_with_master
import datetime
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
        game_master, game = make_game_with_master(self.session)
        games_from_db = self.session.query(Game).all()
        self.assertEqual(1, len(games_from_db))
        self.assertEqual(game, games_from_db[0]) 
    
    def test_game_start(self):
        game_master, game = make_game_with_master(session=self.session, add_gm_to_game=False)
        self.assertFalse(game.started)
        
        #There's only one user, so the game can't start
        
        self.assertRaises(InvalidGameRosterException, game.start)
        
        #Add a user, and the game still can't start because gamemasters can't play
        users = make_users(2, self.session)
        game.add_user(users[0])
        self.assertRaises(InvalidGameRosterException, game.start)
        
        #Add the second player, can't start because although there's 2 players, there's no gamemaster
        game.add_user(users[1])
        self.assertRaises(InvalidGameRosterException, game.start)
        
        #Add game master and we can finally play
        game.add_game_master(game_master)
        game.start()
        self.assertTrue(game.started)
        
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
        players = make_users(2, self.session)
        self.session.add(game)
        self.session.flush()
        
        mission = Mission(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id)
                      
        self.session.add(mission)
        self.session.flush()
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
        
    def test_shot_count_and_timing(self):
        game_master, game = make_game_with_master(self.session, True)
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
        self.session.add(valid_shot)
        self.session.flush()
        self.assertTrue(valid_shot.is_valid())
        self.assertEqual(2, players[0].get_shots_remaining(game.id)) #make sure the user only has 2 shots left
        
        #wait 89 minutes, and fire another shot.  Shouldn't work because it hasn't been 90 minutes.
        invalid_shot = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W",
                      timestamp=datetime.datetime.now()+datetime.timedelta(minutes=89))
        self.session.add(invalid_shot)
        self.session.flush()
        self.assertEqual(2, players[0].get_shots_remaining(game.id))#the shot wasn't valid, so it shouldn't have been subtracted
        self.assertFalse(invalid_shot.is_valid())
        
        #wait 90 minutes from the valid shot and fire again.  This should work.
        valid_shot2 = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W",
                      timestamp=datetime.datetime.now()+datetime.timedelta(minutes=90))
        self.session.add(valid_shot2)
        self.session.flush()
        self.assertTrue(valid_shot2.is_valid())
        self.assertEqual(1, players[0].get_shots_remaining(game.id))
        
        #wait 90+89 minutes, and fire another shot.  Shouldn't work because it hasn't been 90 minutes from valid shot 2.
        invalid_shot = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W",
                      timestamp=datetime.datetime.now()+datetime.timedelta(minutes=90 + 89))
        self.session.add(invalid_shot)
        self.session.flush()
        self.assertEqual(1, players[0].get_shots_remaining(game.id))#the shot wasn't valid, so it shouldn't have been subtracted
        self.assertFalse(invalid_shot.is_valid())
        
        #wait 90+90 minutes from the valid shot and fire again.  This should work and is their LAST shot for the day.
        valid_shot3 = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W",
                      timestamp=datetime.datetime.now()+datetime.timedelta(minutes=90 + 90))
        self.session.add(valid_shot3)
        self.session.flush()
        self.assertTrue(valid_shot3.is_valid())
        self.assertEqual(0, players[0].get_shots_remaining(game.id))
        
        #wait 90+90+89 minutes, and fire another shot.  Shouldn't work because they've used their 3 shots for the day!
        invalid_shot = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W",
                      timestamp=datetime.datetime.now()+datetime.timedelta(minutes=90 + 90 + 89))
        self.session.add(invalid_shot)
        self.session.flush()
        self.assertEqual(0, players[0].get_shots_remaining(game.id))#the shot wasn't valid, so it shouldn't have been subtracted
        self.assertFalse(invalid_shot.is_valid())
        
        #wait 90+90+90 minutes from the valid shot and fire again.  This should still not work because they've used 3 shots!
        valid_shot3 = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W",
                      timestamp=datetime.datetime.now()+datetime.timedelta(minutes=90 + 90 + 90))
        self.session.add(valid_shot3)
        self.session.flush()
        self.assertFalse(valid_shot3.is_valid())
        self.assertEqual(0, players[0].get_shots_remaining(game.id))
        
        #wait 24 hours and fire another shot.  Should work because it has been 24 minutes from first valid shot.
        #They still haven't recovered from their other 2 shots, however, so they have no remaining shots.
        valid_shot4 = Shot(assassin_id=players[0].id, \
                     target_id=players[1].id, \
                      game_id=game.id,
                      shot_picture=shot_picture,
                      assassin_gps="1234567N;12345678W",
                      timestamp=datetime.datetime.now()+datetime.timedelta(minutes=24 * 60))
        self.session.add(valid_shot4)
        self.session.flush()
        self.assertEqual(0, players[0].get_shots_remaining(game.id))#they should have only had 1 valid shot, and now it's 0
        self.assertFalse(valid_shot4.is_valid())
        
class TestDispute(BaseTest):
    def test_create_dispute(self):
        
        #make a game, add some users to it, start it
        game_master, game = make_game_with_master(self.session)
        users = make_users(3, self.session)
        game.add_users(users)
        game.start()
        
        #The assassin shoots his target
        an_active_mission = game.get_missions(active_only=True)[0]
        bogus_shot = Shot(assassin_id=an_active_mission.assassin_id, \
             target_id=an_active_mission.target_id, \
              game_id=game.id,
              shot_picture="http://www.imgur.com/bogusShot.png")
        
        #No disputes yet
        self.assertEqual(0, len(get_disputes(game_id=game.id)))
        
        #The target sees the supposed kill picture, but it's just a picture of Tard the Grumpy Cat, not of him being shot
        dispute = Dispute(claim='This is just a picture of tard the grumpy cat!', game_id=game.id, shot_id=bogus_shot.id)
        
        self.session.add(dispute)
        self.session.add(bogus_shot)
        self.session.flush()
        
        disputes_from_db = get_disputes(game_id=game.id)
        self.assertEqual(1, len(disputes_from_db))
        self.assertEqual(dispute, disputes_from_db[0])
        
        
        
    def test_resolve_dispute_by_gm(self):
        pass
    pass

class TestPowerup(BaseTest):
    def test_create_powerup(self):
        
        # Create 3 powerups and add them to the table
        dbl_shot_pwr = Powerup('double_shot', 3)
        reload_pwr = Powerup('fast_reload', 3)
        bdy_dbl_pwr = Powerup('body_double', 5)
        
        self.session.add(dbl_shot_pwr)
        self.session.add(reload_pwr)
        self.session.add(bdy_dbl_pwr)
        self.session.flush()
        
        # Test to confirm the powerups are in the table
        self.assertEquals(dbl_shot_pwr, self.session.query(Powerup).filter_by(title=dbl_shot_pwr.title).one())
        self.assertEquals(reload_pwr, self.session.query(Powerup).filter_by(title=reload_pwr.title).one())
        self.assertEquals(bdy_dbl_pwr, self.session.query(Powerup).filter_by(title=bdy_dbl_pwr.title).one())
        
    def test_enable_powerup(self):
        
        # Will have to create powerups, add them to database, then create a
        # game w/ gamemaster and confirm gamemaster can enable powerups
        
        # creating powerups
        dbl_shot_pwr = Powerup('double_shot', 3)
        reload_pwr = Powerup('fast_reload', 3)
        bdy_dbl_pwr = Powerup('body_double', 5)
        
        self.session.add(dbl_shot_pwr)
        self.session.add(reload_pwr)
        self.session.add(bdy_dbl_pwr)
        self.session.flush()
        
        # create game w/ gamemaster
        game_master, game = make_game_with_master(self.session)
        self.session.flush()
        
        # Enable Powerups for game
        game.disable_powerup(game_master.id, dbl_shot_pwr.id)
        self.assertFalse(self.session.query(Game).filter_by(id=game.id).value('double_shot'))
        
        game.disable_powerup(game_master.id, reload_pwr.id)
        self.assertFalse(self.session.query(Game).filter_by(id=game.id).value('fast_reload'))
        
        game.disable_powerup(game_master.id, bdy_dbl_pwr.id)
        self.assertFalse(self.session.query(Game).filter_by(id=game.id).value('body_double'))
        
    def test_purchase_powerup(self):
        # Steps for testing
        # Step 0: Create 3 powerups and add them to table
        # Step 1: Create a game and gamemaster
        # Step 2: Enable a powerup for the game
        # Step 3: Add users to the game
        # Step 4: Start game
        # Step 5: Can users see enabled powerup(s)?
        # Step 6: Can users buy a powerup?
        # Step 7: Exception if they cannot buy?
        # Step 8: Confirm each powerup has the desired effect on player
        
        # Step 0: Create 3 powerups and add them to the table
        dbl_shot_pwr = Powerup('double_shot', 3)
        reload_pwr = Powerup('fast_reload', 3)
        bdy_dbl_pwr = Powerup('body_double', 5)
        
        self.session.add(dbl_shot_pwr)
        self.session.add(reload_pwr)
        self.session.add(bdy_dbl_pwr)
        self.session.flush()
        
        # Step 1: Create a game and gamemaster
        game_master, game = make_game_with_master(self.session)
        
        # Step 2: Enable a powerup for the game
        #game.disable_powerup(game_master.id, dbl_shot_pwr.id)
        
        # Step 3: Add users to the game
        users = make_users(2, self.session)
        game.add_user(users[0])
        game.add_user(users[1])
        
        # Step 4: Start game
        game.start()
        
        # Step 5: Can users see enabled powerup(s)?
        enabled_powerups = game.list_enabled_powerups()
        self.assertListEqual([dbl_shot_pwr], enabled_powerups)
        
        # Step 6: Can users buy a powerup?
        purchase_powerup(users[0].id, game.id, dbl_shot_pwr.id)
        self.assertTrue(self.session.query(UserGame).filter_by(user_id=users[0].id, game_id=game.id).value('has_double_shot'))
        
        # Step 7: Check for exceptions
        # Buying the same powerup
        self.assertRaises(PowerupException, purchase_powerup, users[0].id, game.id, dbl_shot_pwr.id)
        # Not enough money
        self.assertRaises(PowerupException, purchase_powerup, users[0].id, game.id, bdy_dbl_pwr.id)
        usergame = get_usergame(user_id=users[1].id, game_id=game.id)
        usergame.money = 0
        # No money
        self.assertRaises(PowerupException, purchase_powerup, users[1].id, game.id, dbl_shot_pwr.id)
        # Caller Dead
        usergame.money = 50
        usergame.alive = False
        self.assertRaises(PowerupException, purchase_powerup, users[1].id, game.id, dbl_shot_pwr.id)
        
        # Step 8: Confirm powerup effects
        usergame.alive = True
        self.assertEqual(MAX_SHOTS_PER_24_HOURS*2, self.session.query(UserGame).filter_by(user_id=users[0].id, game_id=game.id).value('max_shots_per_24_hours'))
        purchase_powerup(users[1].id, game.id, bdy_dbl_pwr.id)
        self.assertTrue(self.session.query(UserGame).filter_by(user_id=users[1].id, game_id=game.id).value('has_body_double'))
        
        purchase_powerup(users[1].id, game.id, reload_pwr.id)
        shot_interval = self.session.query(UserGame).filter_by(user_id=users[1].id, game_id=game.id).value('max_shot_interval_minutes')
        self.assertEqual(MAX_SHOT_INTERVAL_MINUTES/2, shot_interval)

def suite():
    user_tests = unittest.TestLoader().loadTestsFromTestCase(TestUser)
    game_tests = unittest.TestLoader().loadTestsFromTestCase(TestGame)
    kill_tests = unittest.TestLoader().loadTestsFromTestCase(TestKill)
    shot_tests = unittest.TestLoader().loadTestsFromTestCase(TestShot)
    dispute_tests = unittest.TestLoader().loadTestsFromTestCase(TestDispute)
    mission_tests = unittest.TestLoader().loadTestsFromTestCase(TestMission)
    powerup_tests = unittest.TestLoader().loadTestsFromTestCase(TestPowerup)
    return unittest.TestSuite([user_tests, game_tests, kill_tests, shot_tests, dispute_tests, mission_tests, powerup_tests])
