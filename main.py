#	Sample main.py Tornado file
# 
#	Author: Mike Dory
#		11.12.11
#

#!/usr/bin/env python
from modelhandlers import StatsHandler
from tornado.options import define, options
import logging
import os
import os.path
import tornado.escape
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
			(r"/([^/]+)?", MainHandler),
			(r"/account/createuser", AccountHandlers.CreateUserHandler),
			(r"/account/login", AccountHandlers.LoginHandler),
			(r"/game/creategame", GameActionHandlers.CreateGame),
			(r"/game/viewmission", GameActionHandlers.ViewMission),
			(r"/game/viewallmissions", GameActionHandlers.ViewAllMissions),
			(r"/game/assassinate", GameActionHandlers.Assassinate),
			(r"/game/disputes/view", GameActionHandlers.StatsHandler),
			(r"/game/disputes/resolve", GameActionHandlers.StatsHandler),
			(r"/game/kills/view", GameActionHandlers.StatsHandler),
			(r"/game/join", GameActionHandlers.StatsHandler),
			(r"/game/powerup/buy", PowerupHandlers.StatsHandler),
			(r"/game/powerup/activate", PowerupHandlers.StatsHandler),
			(r"/game/powerup/inventory", PowerupHandlers.StatsHandler),
			(r"/game/powerup/viewenabled", PowerupHandlers.StatsHandler),
			(r"/game/master/kick", GameMasterHandlers.StatsHandler),
			(r"/game/master/grantpowerup", GameMasterHandlers.StatsHandler),
			
		]
		settings = dict(
			template_path=os.path.join(os.path.dirname(__file__), "templates"),
			static_path=os.path.join(os.path.dirname(__file__), "static"),
			debug=True,
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


# RAMMING SPEEEEEEED!
def main():
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(os.environ.get("PORT", 5000))

	# start it up
	tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
	main()