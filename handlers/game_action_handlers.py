from models import User, Item, Session, UserGame
from pkg_resources import StringIO
from sqlalchemy.sql.functions import random
import dbutils
import os
import simplejson
import tornado

#logger = logging.getLogger('modelhandlers')

"""
username
item_id
<file>
"""
class CreateGame(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self):
        friendly_name = self.get_argument('friendly_name', True)
        game_master_username = self.get_argument('username')
        base_money = int(self.get_argument('base_money'))
        session = Session()
        try:
            user = dbutils.get_or_create(session, User, username=username)
            games_entered = session.query(UserGame).filter_by(user_id=user.id).all()
            final_string = "User has entered %d" % len(games_entered)
        except Exception, e:
            session.rollback()
            final_string = "Oops!  Something went wrong.  Please try again"
        finally:
            Session.remove()
            self.finish(final_string)


"""
username
"""
class ViewMission(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        username = self.get_argument('username')
        game_id = self.get_argument('game_id')
        mission_id = self.get_argument('mission_id', None)
        session = Session()
        try:
            pass
        except Exception, e:
            session.rollback()
        Session.remove()
        self.finish(simplejson.dumps())

"""
username
"""
class ViewAllMissions(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        username = self.get_argument('username')

        session = Session()
        try:
            user = dbutils.get_or_create(session, User, username=username)
            final_string = "User creation successful!"
        except Exception, e:
            session.rollback()
            final_string = "User creation failed."
        finally:
            Session.remove()
            self.finish(final_string)

class Assassinate(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        username = self.get_argument('username')
        game_id = self.get_argument('game_id')
        shot_picture = None
        target_username = self.
        mission_id = self.get_argument('mission_id', None)
        session = Session()
        try:
            finish_string = "Item added"
#            completed_items = session.Query(ItemCompletion).filter()
        except Exception, e:
            session.rollback()
            finish_string = "Item not added"
        finally:
            Session.remove()
            self.finish(finish_string)

class DisputeHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        item_id = self.get_argument('itemid')
        description = self.get_argument('description', '')

        session = Session()
        try:
            item = dbutils.get_or_create(session, Item, item_id=item_id)
            item.description = description
            session.add(item)
            session.flush()
            session.commit()
            finish_string = "Item added"
#            completed_items = session.Query(ItemCompletion).filter()
        except Exception, e:
            session.rollback()
            finish_string = "Item not added"
        finally:
            Session.remove()
            self.finish(finish_string)

class ViewKills(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        item_id = self.get_argument('itemid')
        description = self.get_argument('description', '')

        session = Session()
        try:
            item = dbutils.get_or_create(session, Item, item_id=item_id)
            item.description = description
            session.add(item)
            session.flush()
            session.commit()
            finish_string = "Item added"
#            completed_items = session.Query(ItemCompletion).filter()
        except Exception, e:
            session.rollback()
            finish_string = "Item not added"
        finally:
            Session.remove()
            self.finish(finish_string)

class JoinGame(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        item_id = self.get_argument('itemid')
        description = self.get_argument('description', '')

        session = Session()
        try:
            item = dbutils.get_or_create(session, Item, item_id=item_id)
            item.description = description
            session.add(item)
            session.flush()
            session.commit()
            finish_string = "Item added"
#            completed_items = session.Query(ItemCompletion).filter()
        except Exception, e:
            session.rollback()
            finish_string = "Item not added"
        finally:
            Session.remove()
            self.finish(finish_string)
            