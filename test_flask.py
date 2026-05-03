from app import app, db, User, Request
import unittest

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        # Set up the Flask application and test client
        self.app = app
        self.client = app.test_client()
        with app.app_context():
            # Clear the database
            db.session.query(Request).delete()
            db.session.query(User).delete()
            db.session.commit()

            # Add a test user
            user = User(
                username='testuser',
                email='test@example.com',
                role='customer'
            )
            user.set_password('testpassword')
            db.session.add(user)
            db.session.commit()

    def tearDown(self):
        # Tear down the database after each test
        with app.app_context():
            db.session.query(Request).delete()
            db.session.query(User).delete()
            db.session.commit()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_login(self):
        response = self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 200)

    def test_register(self):
        response = self.client.post('/register', data={
            'email': 'newuser@example.com',
            'username': 'newuser',
            'password': 'newpassword',
            'role': 'customer'
        })
        self.assertEqual(response.status_code, 200)

    def test_submit_cleaning_request(self):
        # Log in first
        self.client.post('/login', data={
            'email': 'test@example.com',
            'password': 'testpassword'
        })

        # Submit a cleaning request
        response = self.client.post('/submit-cleaning-request', json={
            'cart': [
                {'service': 'Basic Cleaning', 'photo': 'photo_path', 'description': 'Clean the kitchen'}
            ]
        })
        self.assertEqual(response.status_code, 302)  # Redirect to cart page
