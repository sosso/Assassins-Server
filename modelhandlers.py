from models import User, Item, ItemCompletion, Session, UserGame
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
class StatsHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        username = self.get_argument('username')
#        item_id = self.get_argument('item_id')
#        try: file1 = self.request.files['file'][0]
#        except: file1 = None

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
class GetCompletedItemsHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        username = self.get_argument('username')

        session = dbutils.Session()
        try:
            user = dbutils.get_or_create(session, User, username=username)
            item_array = []
            for item_completion in user.completed_items:
                item = item_completion.item
                info_dict = item.serialize()
                if item_completion.file_path is not None:
                    info_dict['image'] = item_completion.file_path
                else:
                    info_dict['image'] = ''
                item_array.append(info_dict)
#            completed_items = session.Query(ItemCompletion).filter()
        except Exception, e:
            session.rollback()
        dbutils.Session.remove()
        self.finish(simplejson.dumps(item_array))

"""
username
"""
class CreateUserHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        username = self.get_argument('username')

        session = dbutils.Session()
        try:
            user = dbutils.get_or_create(session, User, username=username)
            final_string = "User creation successful!"
        except Exception, e:
            session.rollback()
            final_string = "User creation failed."
        finally:
            dbutils.Session.remove()
            self.finish(final_string)

class DefineItemHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        item_id = self.get_argument('itemid')
        description = self.get_argument('description', '')

        session = dbutils.Session()
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
            dbutils.Session.remove()
            self.finish(finish_string)


