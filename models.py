from sqlalchemy import Column, Integer, VARCHAR, INTEGER
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, scoped_session
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.schema import ForeignKey
from sqlalchemy.types import String
import dbutils

#engine = create_engine('mysql://bfc1ffabdb36c3:65da212b@us-cdbr-east-02.cleardb.com/heroku_1cec684f35035ce', echo=True, pool_recycle=3600)#recycle connection every hour to prevent overnight disconnect)
engine = create_engine('mysql://anthony:fr13nd30@localhost:3306/assassins', echo=True, pool_recycle=3600)#recycle connection every hour to prevent overnight disconnect)
Base = declarative_base(bind=engine)
sm = sessionmaker(bind=engine, autoflush=True, autocommit=False, expire_on_commit=False)
Session = scoped_session(sm)

class User(Base):
    __tablename__ = 'user'
    #column definitions
    id = Column(u'id', INTEGER(), primary_key=True, nullable=False)
    username = Column(u'username', VARCHAR(length=255), nullable=False)
    password = Column(u'password', VARCHAR(length=255), nullable=False)
    profile_picture = Column(u'profile_picture', VARCHAR(length=255), nullable=False)
    
    def User(self, password, username, profile_picture):
        self.username = username
        self.password = password
        self.profile_picture = profile_picture

#    item_completions = relationship('ItemCompletion', backref='user') #one to many
#    completed_items = association_proxy('completed_items', 'item')
    # user.completed_items.append(foo_item)

class ItemCompletion(Base):
    __tablename__ = 'itemcompletion'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    item_id = Column(Integer, ForeignKey('item.id'), primary_key=True)
    file_path = Column(VARCHAR(255))

#    user = relationship(User, backref=backref("completed_items", cascade="all, delete-orphan"))
#    item = relationship("Item")
    #Session().Query(Item).filter_by(item.id==self.item_id)

    def __init__(self, user_id, item_id, file_path=None):
        self.user_id = user_id
        self.item_id = item_id
        self.file_path = file_path

    def __repr__(self):
        return '<ItemCompletion %d @ %d>' % (self.user_id, self.item_id)


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer)
    description = Column(VARCHAR(length=255))

    def __init__(self, item_id, description=''):
        self.item_id = item_id
        self.description = description

    def __repr__(self):
        return '<Item %d>' % self.item_id

    def serialize(self):
        return {'Item number': self.item_id,
                'Description': self.description
                }

Base.metadata.create_all(engine)


