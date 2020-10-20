import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class UserViewTestCase(TestCase):
    """Test views for users"""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="password",
                                    image_url=None)
        self.testuser_id = 100
        self.testuser.id = self.testuser_id

        self.u1 = User.signup("abc", "test1@test.com", "password", None)
        self.u1_id = 778
        self.u1.id = self.u1_id
        self.u2 = User.signup("efg", "test2@test.com", "password", None)
        self.u2_id = 884
        self.u2.id = self.u2_id
        self.u3 = User.signup("hij", "test3@test.com", "password", None)
        self.u4 = User.signup("testing", "test4@test.com", "password", None)

        db.session.commit()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_list_users(self):
        """List all users"""

        with self.client as c:
            resp = c.get('/users')
            html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('abc', html)
        self.assertIn('efg', html)
        self.assertIn('hij', html)
        self.assertIn('testing', html)
        self.assertIn('testuser', html)

    def test_list_users_search(self):
        """List users matching search query. Do not list other users"""

        with self.client as c:
            resp = c.get('/users?q=test')
            html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('testing', html)
        self.assertIn('testuser', html)

        self.assertNotIn('abc', html)
        self.assertNotIn('efg', html)
        self.assertNotIn('hij', html)
        
    def test_users_show(self):
        """Is the correct user profile being returned?"""   

        with self.client as c:
            resp = c.get('/users/100')
            html = resp.get_data(as_text=True) 

        self.assertEqual(resp.status_code, 200)
        self.assertIn('testuser', html)

    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        f3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()

    def test_show_following(self):
        """Are the correct profiles showing/not showing?"""

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/100/following")
            html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("@abc", html)
        self.assertIn("@efg", html)

        self.assertNotIn("@hij", html)
        self.assertNotIn("@testing", html)

    def test_show_followers(self):
        """Are the correct profiles showing/not showing?"""

        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/100/followers")
            html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("@abc", html)

        self.assertNotIn("@efg", html)
        self.assertNotIn("@hij", html)
        self.assertNotIn("@testing", html)

    def test_add_follow(self):
        """Can a logged in user successfully follow another profile?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.post('/users/follow/778', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            follow = Follows.query.filter(Follows.user_being_followed_id == 778, Follows.user_following_id == 100)
            self.assertIsNotNone(follow)

            self.assertIn('@abc', html)
            
            self.assertNotIn('@efg', html)
            self.assertNotIn("@hij", html)
            self.assertNotIn("@testing", html)

    def test_stop_following(self):
        """Can a logged in user successfully stop following a profile they are currently following?"""

        f1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        db.session.add(f1)
        db.session.commit()
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

        resp = c.post('/users/stop-following/778', follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)

        follow = Follows.query.filter(Follows.user_being_followed_id == 778, Follows.user_following_id == 100).first()
        self.assertIsNone(follow)

    def setup_likes(self):
        m1 = Message(text="trending warble", user_id=self.testuser_id)
        m2 = Message(text="Eating some lunch", user_id=self.testuser_id)
        m3 = Message(id=999, text="likable warble", user_id=self.u1_id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.testuser_id, message_id=999)

        db.session.add(l1)
        db.session.commit()

    def test_show_users_likes(self):
        """Are the correct liked messages being shown?"""

        self.setup_likes()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f"/users/100/likes")
            html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('@abc', html)

        self.assertNotIn("@efg", html)
        self.assertNotIn("@hij", html)
        self.assertNotIn("@testing", html)

    def test_update_profile(self):
        """Can an authenticated user successfully update their profile?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser_id

            d = {'username': 'testuser', 'password': 'password', 'email': 'new@test.com', 'bio': 'test bio'}
            resp = c.post('/users/profile', data=d, follow_redirects=True)
            html = resp.get_data(as_text=True)

            curr_user = User.query.get(sess[CURR_USER_KEY])

            self.assertEqual(resp.status_code, 200)
            self.assertEqual(curr_user.email, 'new@test.com')
            self.assertIn('test bio', html)




    



    

    







         
        