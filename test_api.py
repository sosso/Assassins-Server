from test_utils import APIBaseTest
import requests
import simplejson
import unittest



base_url = 'http://localhost:5000/'
success_dict = {'success':'success'}
exists_dict = {u'reason': u'Account already exists', u'success': u'error'}
files = {'profile_picture': open('test.png', 'rb').read()}
test_game_password = 'test_game_password'

def create_users(count=1):
    reqs = []
    for usernumber in range(count):
        reqs.append(requests.post(base_url + 'account/createuser?username=test_user%d&password=test_pass' % usernumber, files=files))#create, then make again
    return reqs

def create_game():
    create_users()
    payload = {'friendly_name': 'test game', 'game_master_username': 'test_user0', \
                       'secret_token':'test_pass', 'game_password':'test_game_password', 'base_money':6}
    r = requests.post(base_url + 'game/creategame?', params=payload)
    return r

def join_game(game_req, user_req):
    payload = {'game_id':game_req.json['game_id'], 'game_password':test_game_password, \
                    'username':'test_user1', 'secret_token':'test_pass'}
    r = requests.post(base_url + 'game/?', params=payload)
    return r

class TestUser(APIBaseTest):
    
    def test_user_creation(self):
        create_users(1)
        r = requests.post(base_url + 'account/createuser?username=test_user0&password=test_pass', files=files)
        self.assertEqual(success_dict, simplejson.loads(r.text))

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
        self.assertTrue(len(games_list.json) > 0)
        pass
        

def suite():
    user_tests = unittest.TestLoader().loadTestsFromTestCase(TestUser)
    game_tests = unittest.TestLoader().loadTestsFromTestCase(TestGame)
    return unittest.TestSuite([user_tests, game_tests])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
