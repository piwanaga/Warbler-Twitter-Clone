"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test User model"""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(len(u.following), 0)
        
        """Does the repr method work as expected?"""
        self.assertIn('testuser', repr(User(username='testuser')))

    def test_is_following(self):
        """Does is_following successfully detect when user1 is following user2?"""

        u1 = User(
            email="test1@test.com",
            username="user1",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="user2",
            password="HASHED_PASSWORD"
        )

        db.session.add_all([u1, u2])
        db.session.commit()

        u1.following.append(u2)
        db.session.commit()

        # u1 should be following u2, u2 should not be following u1
        self.assertTrue(User.is_following(u1, u2))
        self.assertFalse(User.is_following(u2, u1))

    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when user1 is followed by user2?"""

        u1 = User(
            email="test1@test.com",
            username="user1",
            password="HASHED_PASSWORD"
        )

        u2 = User(
            email="test2@test.com",
            username="user2",
            password="HASHED_PASSWORD"
        )

        db.session.add_all([u1, u2])
        db.session.commit()

        u1.followers.append(u2)
        db.session.commit()

        # u2 should be following u1. u1 should not be following u2
        self.assertTrue(User.is_followed_by(u1, u2))
        self.assertFalse(User.is_followed_by(u2, u1))

    def test_signup(self):
        """Does User.signup successfully create a new uer given valid credentials?"""

        u = User.signup('testuser', 'test@test.com', 'HASHED_PASSWORD', 'test.com')

        db.session.add(u)
        db.session.commit()

        self.assertIsInstance(User.query.get(u.id), User)
        self.assertEqual(u.username, 'testuser')
        
    def test_signup_fail(self):
        """Does User.signup fail to create a new uer given invalid credentials? i.e. in the case below, and omitted password"""
        
        self.assertRaises(TypeError, User.signup, 'testuser', 'test@test.com')

    def test_authenticate(self):
        """Does User.authenticate successfully return a user given valid credentials"""

        u = User.signup('testuser', 'test@test.com', 'HASHED_PASSWORD', 'test.com')

        db.session.add(u)
        db.session.commit()
        
        self.assertEqual(User.authenticate('testuser', 'HASHED_PASSWORD'), u)


        """Does User.authenticate fail to return a user when the username is invalid?"""

        self.assertEqual(User.authenticate('testuser1', 'HASHED_PASSWORD'), False)

        """Does User.authenticate fail to return a user when the password is invalid?"""
        
        self.assertEqual(User.authenticate('testuser', 'PASSWORD'), False)