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
from app.database import get_db # For clearing collections
import mongomock
from unittest.mock import patch

class BaseTestCase(unittest.TestCase):
    @patch('app.database.MongoClient') # Patch MongoClient constructor in app.database
    def setUp(self, mock_mongo_constructor):
        # Create a single mongomock client instance for the test
        self.mock_mongo_client = mongomock.MongoClient()
        # Configure the mock constructor to return our mongomock client instance
        mock_mongo_constructor.return_value = self.mock_mongo_client

        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['DEBUG'] = False
        # Use a temporary directory for UPLOAD_FOLDER during tests
        self.temp_upload_folder = tempfile.mkdtemp()
        self.app.config['UPLOAD_FOLDER'] = self.temp_upload_folder
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # create_dummy_users will now use the mongomock client because
        # app.database.get_mongo_client() will use the mocked MongoClient
        # which returns our self.mock_mongo_client.
        models.create_dummy_users()

    def tearDown(self):
        # Clear mongomock collections after each test
        # Ensure an app context is active for get_db() to work correctly
        # (it relies on current_app and g)
        
        # The app_context is pushed in setUp and should be popped here.
        # The main app_context is self.app_context, pushed in setUp.
        # We must ensure it's the one active when calling get_db().
        
        with self.app_context: # Ensure operations are within the main app context
            db = get_db() # This will use the mongomock client
            # Mongomock's MongoClient can have databases dropped directly
            # Or clear specific collections as done before.
            # For simplicity and thoroughness, let's get the db_name from config
            # and drop that database from the mock client.
            db_name = self.app.config.get('DATABASE_NAME', 'flask_db') # Default from config.py
            if self.mock_mongo_client and db_name:
                self.mock_mongo_client.drop_database(db_name)

        self.app_context.pop() 
        shutil.rmtree(self.temp_upload_folder)
        # The patch applied via decorator to setUp stops automatically.

    def login_as(self, username, password):
        response = self.client.post('/login', json={'username': username, 'password': password})
        self.assertEqual(response.status_code, 200, msg=f"Login failed: {response.get_data(as_text=True)}")
        data = response.get_json()
        self.assertIn('token', data)
        return data['token']
