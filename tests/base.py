import unittest
import tempfile
import shutil
import os
import sys

# Adjust path to ensure 'app' can be imported
# Assuming tests are run from the project root (expense_platform)
# Adding project root to sys.path allows 'from app import ...'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app import create_app, models

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['DEBUG'] = False
        # Use a temporary directory for UPLOAD_FOLDER during tests
        # This path will be absolute
        self.temp_upload_folder = tempfile.mkdtemp()
        self.app.config['UPLOAD_FOLDER'] = self.temp_upload_folder
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Reset in-memory databases for each test
        models.USERS_DB.clear()
        models.SESSIONS_DB.clear()
        models.EXPENSES_DB.clear()
        models.create_dummy_users() # Re-populate with standard dummy users

    def tearDown(self):
        self.app_context.pop()
        # Remove the temporary upload folder
        shutil.rmtree(self.temp_upload_folder)

    def login_as(self, username, password):
        response = self.client.post('/login', json={'username': username, 'password': password})
        self.assertEqual(response.status_code, 200, msg=f"Login failed: {response.get_data(as_text=True)}")
        data = response.get_json()
        self.assertIn('token', data)
        return data['token']
