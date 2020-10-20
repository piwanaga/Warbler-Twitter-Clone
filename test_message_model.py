import os
from unittest import TestCase

from models import db, User, Message, Follows

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

db.create_all()

class MessageModelTestCase(TestCase):
    """Test Message model"""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        self.user = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(self.user)
        db.session.commit()

    def test_message_model(self):
        """Does basic model work?"""

        # User should have no messages and no followers
        self.assertEqual(len(self.user.messages), 0)
        self.assertEqual(len(self.user.followers), 0)
        self.assertEqual(len(self.user.following), 0)

        m = Message(text='test', user_id=self.user.id)

        db.session.add(m)
        db.session.commit()

        """Does a new message succesfully get added to db given valid credentials?"""
        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.user.messages[0].text, 'test')

    def test_add_message_fail(self):
        """Does a new message fail to get added given invalid credentials?"""

        def add_message(text, user_id):
            m = Message(text=text, user_id=user_id)
            return m

        # Trying to create a new message with missing data such as a user_id should raise an error
        self.assertRaises(TypeError, add_message, 'test')
        

