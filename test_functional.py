from models import Game, Mission, Shot
from test_utils import BaseTest, make_users
import datetime
import unittest

class TestGameplay(BaseTest):
    def test_gameplay(self):
        #Make a game, game master
        game_master = make_users(1)[0]
        self.session.add(game_master)
        self.session.flush()
        game = Game(title='test game', password='testpassword', starting_money=3, game_master_id=game_master.id)
        self.session.add(game)
        games_from_db = self.session.query(Game).all()
        self.assertEqual(1, len(games_from_db))
        self.assertEqual(game, games_from_db[0]) 
        
        #Make 4 players, and add them to the game.
        #Don't start the game yet; make sure no missions exist until we start.
        players = make_users(4)
        self.session.add_all(players)
        game.add_users(players)
        self.assertEqual(0, len(game.get_missions()))
        game.start()
        #Now that we've started, each player should have a target, so there should be 4 missions
        self.assertEqual(4, len(game.get_missions()))
        
        #Get player 0's mission, and then shoot his target
        player_0_mission = self.session.query(Mission).filter_by(game_id=game.id, assassin_id=players[0].id).one()
        
        #Grab player 0's target's mission to make sure reassignment works
        player_0s_target_id = player_0_mission.target_id
        player_0s_targets_mission = self.session.query(Mission).filter_by(game_id=game.id, assassin_id=players[0].id).one()
        
        
        player_0_shooting_target = Shot(assassin_id=players[0].id,\
                                        target_id=player_0_mission.target_id,\
                                        game_id=game.id,\
                                        shot_picture='www.foo.com/headshot.jpg')
        self.assertTrue(player_0_shooting_target.is_valid())
        
        #THIS CAN BE REFACTORED AND PROBABLY SHOULD BE
        pre_confirm_timestamp = datetime.datetime.now()
        player_0_shooting_target.confirm_kill()
        game.mission_completed(player_0_mission)
        #Make sure the mission's completion time is updated when mission is confirmed
        self.assertTrue(player_0_mission.completed_timestamp - player_0_mission.assignment_timestamp < datetime.timedelta(seconds=10))
        
        #Get player 0's new mission.  It should not be completed because that player is still alive since player 0's target did not kill his target.
        player_0_new_mission = self.session.query(Mission).filter_by(game_id=game.id, assassin_id=players[0].id, completed_timestamp=None).one()
        #Make sure that player 0's new mission is targeting whoever his original target was targeting
        self.assertEqual(player_0_new_mission.target_id, player_0s_targets_mission.target_id)
        

def suite():
    gameplay_tests = unittest.TestLoader().loadTestsFromTestCase(TestGameplay)
    return unittest.TestSuite(gameplay_tests)
