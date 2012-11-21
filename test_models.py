from models import User, Session
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker
import unittest
import bcrypt

class TestUser(unittest.TestCase):
    
    def teardown(self):
        Session.remove()
        
    def test_user_creation(self):
        session = Session()
        u = User(username='Hitman', password='123456', profile_picture='hitman.png')
        session.add(u)
        self.assertEqual(1, len(session.query(User).filter_by(username='Hitman').all()))
        
if __name__ == '__main__':
    unittest.main()
