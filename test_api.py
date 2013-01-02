from models import populate_powerups, Session, Powerup, get_usergame, get_user
from test_utils import APIBaseTest
import os
import requests
import simplejson
import unittest



base_url = 'http://127.0.0.1:' + os.environ.get("PORT", 5000)
success_dict = {'success':'success'}
exists_dict = {u'reason': u'Account already exists', u'success': u'error'}
files = {'profile_picture': open('test.png', 'rb').read()}
shot_files = {'shot_picture': open('test.png', 'rb').read()}
test_game_password = 'test_game_password'

def create_users(count=1):
    reqs = []
    for usernumber in range(count):
        reqs.append(requests.post(base_url + 'account/createuser?username=test_user%d&password=test_pass' % usernumber, files=files))  # create, then make again
    return reqs

def get_kills_list(game_req, user_req):
    payload = {'username':user_req.json['username'], 'game_id':game_req.json['game_id'], 'secret_token':'test_pass'}
    return requests.get(base_url + 'game/kills/view?', params=payload)

def assassinate(game_req, assassin_req, target_req):
    payload = {'username':assassin_req.json['username'], \
               'target_username':target_req.json['username'], \
               'game_id':game_req.json['game_id'],
               'secret_token':'test_pass'}
    return requests.post(base_url + 'game/assassinate?', params=payload, files=shot_files)  # create, then make again

def create_game():
    create_users()
    payload = {'friendly_name': 'test game', 'game_master_username': 'test_user0', \
                       'secret_token':'test_pass', 'game_password':'test_game_password', 'base_money':6}
    r = requests.post(base_url + 'game/creategame?', params=payload)
    return r

def join_game(game_req, user_req):
    
    if 'username' not in user_req.json:
        username = user_req.url.split('=')[1].split('&')[0]
    else:
        username = user_req.json['username']
    payload = {'game_id':game_req.json['game_id'], 'game_password':test_game_password, \
                    'username':username, 'secret_token':'test_pass'}
    r = requests.post(base_url + 'game/?', params=payload)
    return r

def start_game(game_req):
    start_req = requests.post(base_url + 'game/master/start?game_id=%s&secret_token=test_pass&game_master_username=test_user0' % game_req.json['game_id'])
    return start_req

class TestUser(APIBaseTest):
    
    def test_user_creation(self):
        create_users()
        r = requests.post(base_url + 'account/createuser?username=test_user0&password=test_pass', files=files)
        self.assertTrue(r.json['success'] == 'success')

    def test_login(self):
        reqs = create_users(1)
        r = requests.post(base_url + 'account/login?username=test_user0&password=test_pass')
        self.assertEqual(success_dict, r.json)

class TestGame(APIBaseTest):
    
    def test_game_creation(self):
        create_users(1)
        
        r = create_game()
        self.assertTrue('game_id' in r.json)
        self.assertTrue(r.json['success'] == 'success')
        
    def test_join_game(self):
        user_reqs = create_users(2)
        game_req = create_game()
        join_req = join_game(game_req, user_reqs[1])
        self.assertEqual(success_dict, join_req.json)
        
    def test_get_games(self):
        game_req = create_game()
        user_reqs = create_users(2)
        join_game(game_req, user_reqs[1])
        games_list = requests.get(base_url + 'game/?username=test_user1&secret_token=test_pass')
        self.assertTrue(isinstance(games_list.json, list))
        self.assertTrue(len(games_list.json) == 1)
        pass

class TestGameMaster(APIBaseTest):
    def test_start_game(self):
        # Create a game, add two additional users, and start it
        user_reqs = create_users(3)
        game_req = create_game()
        join_req_1 = join_game(game_req, user_reqs[1])
        join_req_2 = join_game(game_req, user_reqs[2])
        start_req = start_game(game_req)
        self.assertEqual(success_dict, start_req.json)

class TestKillView(APIBaseTest):
    def test_view_kills(self):
        user_reqs = create_users(3)
        game_req = create_game()
        join_req_1 = join_game(game_req, user_reqs[1])
        join_req_2 = join_game(game_req, user_reqs[2])
        start_req = start_game(game_req)         
        assassin_req = assassinate(game_req=game_req, assassin_req=user_reqs[1], target_req=user_reqs[2])
        kills_list_req = get_kills_list(game_req, user_reqs[1])
        self.assertTrue(isinstance(kills_list_req.json, list))
        self.assertTrue(len(kills_list_req.json) == 1)
        pass
    
class TestPowerup(APIBaseTest):
    def test_available_powerups(self):
        populate_powerups()
        
        game_req = create_game()
        payload = {'username':'test_user0', 'game_id':game_req.json['game_id'], \
                   'secret_token':'test_pass'}
        powerups_enabled_req = requests.get(base_url + 'game/powerup/available?', params=payload)
        self.assertTrue(isinstance(powerups_enabled_req.json, list))
        self.assertTrue(len(powerups_enabled_req.json) == 3)
        
    def test_disable_powerups(self):
        populate_powerups()
        
        game_req = create_game()
        s = Session()
        powerups = s.query(Powerup).all()       
        
        payload = {'username':'test_user0', 'game_id':game_req.json['game_id'], \
                   'secret_token':'test_pass', 'powerup_id':powerups[0].id}
        powerups_disabled_req = requests.post(base_url + 'game/powerup/disable?', params=payload)
        
        user_req = create_users(2)
        join_req = join_game(game_req, user_req[1])
        
        payload1 = {'username':user_req[1].json['username'], 'game_id':game_req.json['game_id'], \
                    'secret_token':'test_pass'}
        
        powerups_enabled_req = requests.get(base_url + 'game/powerup/available?', params=payload1)
        self.assertTrue(isinstance(powerups_enabled_req.json, list))
        self.assertTrue(len(powerups_enabled_req.json) == 2)
        Session.remove()
        
    def test_purchase_powerup(self):
        populate_powerups()
        
        game_req = create_game()
        s = Session()
        powerups = s.query(Powerup).all()
        
        user_req = create_users(2)
        join_req = join_game(game_req, user_req[1])
        
        payload = {'username':'test_user1', 'game_id':game_req.json['game_id'], \
                   'secret_token':'test_pass', 'item_id':powerups[0].id}
        
        powerup_purchase_req = requests.post(base_url + 'game/powerup/buy?', params=payload)
        
        user = get_user('test_user1')
        user1_game = get_usergame(user.id, game_req.json['game_id'])
        self.assertTrue(user1_game.has_double_shot)
        Session.remove()
        
        
def suite():
    user_tests = unittest.TestLoader().loadTestsFromTestCase(TestUser)
    game_tests = unittest.TestLoader().loadTestsFromTestCase(TestGame)
    gm_tests = unittest.TestLoader().loadTestsFromTestCase(TestGameMaster)
    kill_tests = unittest.TestLoader().loadTestsFromTestCase(TestKillView)
    powerup_tests = unittest.TestLoader().loadTestsFromTestCase(TestPowerup)
    suites = []
#    suites.append(user_tests)
#    suites.append(game_tests)
#    suites.append(gm_tests)
    suites.append(kill_tests)
    suites.append(powerup_tests)
    return unittest.TestSuite(suites)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
