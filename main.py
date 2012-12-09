#	Sample main.py Tornado file
# 
#	Author: Mike Dory
#		11.12.11
#

#!/usr/bin/env python
from tornado.options import define
import handlers.account_handlers as AccountHandlers
import handlers.game_action_handlers as GameActionHandlers
import handlers.game_master_handlers as GameMasterHandlers
import handlers.powerup_handlers as PowerupHandlers
import logging
import os.path
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata

# import and define tornado-y things
define("port", default=5000, help="run on the given port", type=int)
logging.basicConfig()

# application settings and handle mapping info
class Application(tornado.web.Application):
	def __init__(self):
		handlers = [
			(r"/game/creategame", GameActionHandlers.CreateGame),
			(r"/game/viewmission", GameActionHandlers.ViewMission),
			(r"/game/viewallmissions", GameActionHandlers.ViewAllMissions),
			(r"/game/assassinate", GameActionHandlers.Assassinate),
			(r"/game/disputes", GameActionHandlers.DisputeHandler),
			(r"/game/kills/view", GameActionHandlers.ViewKills),
			(r"/game/", GameActionHandlers.GetListOfJoinedOrJoinGame),
			(r"/game/powerup/buy", PowerupHandlers.BuyPowerup),
			(r"/game/powerup/activate", PowerupHandlers.ActivatePowerup),
			(r"/game/powerup/inventory", PowerupHandlers.Inventory),
			(r"/game/powerup/viewenabled", PowerupHandlers.ViewEnabled),
			(r"/game/master/kick", GameMasterHandlers.Kick),
			(r"/game/master/grantpowerup", GameMasterHandlers.GrantPowerup),
			(r"/game/master/start", GameMasterHandlers.Start),
			(r"/account/login", AccountHandlers.LoginHandler),
			(r"/account/createuser", AccountHandlers.CreateUserHandler),
		]
		settings = dict(
			template_path=os.path.join(os.path.dirname(__file__), "templates"),
			static_path=os.path.join(os.path.dirname(__file__), "static"),
			debug=True,
			facebook_secret="dc81b42a8501790580fef05bc11001ae",
			facebook_api_key="383205491767592",
		)
		tornado.web.Application.__init__(self, handlers, **settings)


# the main page
class MainHandler(tornado.web.RequestHandler):
	def get(self, q):
		if os.environ.has_key('GOOGLEANALYTICSID'):
			google_analytics_id = os.environ['GOOGLEANALYTICSID']
		else:
			google_analytics_id = False

		self.render(
			"main.html",
			page_title='Heroku Funtimes',
			page_heading='Hi!',
			google_analytics_id=google_analytics_id,
		)


def main():
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(os.environ.get("PORT", 5000))

	# start it up
	tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
	main()
