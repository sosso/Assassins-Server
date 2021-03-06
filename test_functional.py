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
        game = Game(title='test game', password='testpassword', starting_money=3)
        self.session.add(game)
        self.session.flush()
        game.add_game_master(game_master)
        games_from_db = self.session.query(Game).all()
        self.assertEqual(1, len(games_from_db))
        self.assertEqual(game, games_from_db[0]) 
        
        #Make 3 players, and add them to the game.
        #Don't start the game yet; make sure no missions exist until we start.
        players = make_users(3)
        self.session.add_all(players)
        self.session.flush()
        game.add_users(players)
        self.assertEqual(0, len(game.get_missions()))
        game.start()
        #Now that we've started, each player should have a target, so there should be 3 missions
        self.assertTrue(game.started)
        self.assertEqual(3, len(game.get_missions()))
        
        #Get player 0's mission, and then shoot his target
        player_0_mission = self.session.query(Mission).filter_by(game_id=game.id, assassin_id=players[0].id).one()
        
        #Grab player 0's target's mission to make sure reassignment works
        player_0s_target_id = player_0_mission.target_id
        player_0s_targets_mission = self.session.query(Mission).filter_by(game_id=game.id, assassin_id=player_0s_target_id).one()
        
        #Fire away; this is valid!
        player_0_shooting_target = Shot(assassin_id=players[0].id, \
                                        target_id=player_0_mission.target_id, \
                                        game_id=game.id, \
                                        shot_picture='www.foo.com/headshot.jpg')
        self.session.add(player_0_shooting_target)
        self.session.flush()
        self.assertTrue(player_0_shooting_target.is_valid())
        
#        #Wait 90 minutes and then shoot again; this should work.
#        player_0_shooting_target = Shot(assassin_id=players[0].id, \
#                                        target_id=player_0_mission.target_id, \
#                                        game_id=game.id, \
#                                        shot_picture='www.foo.com/headshot.jpg')
#        self.session.add(player_0_shooting_target)
#        self.session.flush()
#        self.assertTrue(player_0_shooting_target.is_valid())
        
        
        #THIS CAN BE REFACTORED AND PROBABLY SHOULD BE
        pre_confirm_timestamp = datetime.datetime.now()
#        player_0_shooting_target.confirm_kill()
        game.mission_completed(player_0_mission)
        #Make sure the mission's completion time is updated when mission is confirmed
        self.assertTrue(player_0_mission.completed_timestamp - player_0_mission.assignment_timestamp < datetime.timedelta(seconds=10))
        #Game shouldn't be marked completed
        self.assertFalse(game.over)
        
        
        #Get player 0's new mission.  It should not be completed because that player is still alive since player 0's target did not kill his target.
        player_0_new_mission = self.session.query(Mission).filter_by(game_id=game.id, assassin_id=players[0].id, completed_timestamp=None).one()
        #Make sure that player 0's new mission is targeting whoever his original target was targeting
        self.assertEqual(player_0_new_mission.target_id, player_0s_targets_mission.target_id)
        
        #Player 0 waits 90 minutes and kills his second target; the only other remaining player of the game.
        player_0_shooting_target_2 = Shot(assassin_id=players[0].id, \
                                        target_id=player_0_new_mission.target_id, \
                                        game_id=game.id, \
                                        shot_picture='www.foo.com/headshot2.jpg',
                                        timestamp=datetime.datetime.now() + datetime.timedelta(minutes=90))
        self.assertTrue(player_0_shooting_target_2.is_valid())
        self.assertFalse(game.over)
        
        #THIS CAN BE REFACTORED AND PROBABLY SHOULD BE
        pre_confirm_timestamp = datetime.datetime.now()
#        player_0_shooting_target_2.confirm_kill()
        game.mission_completed(player_0_new_mission)
        #Make sure the mission's completion time is updated when mission is confirmed and that it's more recent than the assignment one.
        self.assertTrue(player_0_new_mission.completed_timestamp > player_0_new_mission.assignment_timestamp)
        
        #Now that player 0 has killed the other two players, the game should be over.
        self.assertTrue(game.over)
        #Get the winner User model from the database from the game's get_winner() method and make sure it's player 0.
        self.assertEqual(game.get_winner(), players[0])
        

def suite():
    gameplay_tests = unittest.TestLoader().loadTestsFromTestCase(TestGameplay)
    return unittest.TestSuite(gameplay_tests)
