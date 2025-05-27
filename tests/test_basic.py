import unittest
import json
from io import BytesIO
import os
import sys # Added for path adjustment if needed, though BaseTestCase handles it

# Assuming BaseTestCase is in a 'base.py' sibling file.
# BaseTestCase already adds project_root to sys.path
from tests.base import BaseTestCase 
from app.models import User, Employee, Admin # USERS_DB removed as it's no longer used
from app.storage_services import SIMULATED_CLOUD_FOLDER # To check paths


class TestAuthRoutes(BaseTestCase):
    def test_health_check(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'UP')

    def test_dummy_users_created(self):
        # Dummy users are created in BaseTestCase.setUp via models.create_dummy_users()
        # which now uses mongomock
        self.assertIsNotNone(User.get_by_username("emp1"))
        self.assertIsNotNone(User.get_by_username("admin1"))

    def test_login_employee(self):
        response = self.client.post('/login', json={'username': 'emp1', 'password': 'emp1pass'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('token', data)
        self.assertEqual(data['user']['username'], 'emp1')
        self.assertEqual(data['user']['role'], 'employee')

    def test_login_admin(self):
        response = self.client.post('/login', json={'username': 'admin1', 'password': 'admin1pass'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('token', data)
        self.assertEqual(data['user']['username'], 'admin1')
        self.assertEqual(data['user']['role'], 'admin')

    def test_login_invalid_credentials(self):
        response = self.client.post('/login', json={'username': 'emp1', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 401)

    def test_me_endpoint(self):
        token = self.login_as('emp1', 'emp1pass')
        response = self.client.get('/me', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['username'], 'emp1')

    def test_me_endpoint_no_token(self):
        response = self.client.get('/me')
        self.assertEqual(response.status_code, 401) # Missing token

    # --- New Signup Tests ---
    def test_signup_successful_employee(self):
        # USERS_DB.pop is no longer needed as mongomock collections are cleared in BaseTestCase.tearDown
        response = self.client.post('/signup', json={
            'username': 'newemp',
            'password': 'newpassword123'
        })
        self.assertEqual(response.status_code, 201, msg=response.get_json())
        self.assertEqual(response.json['message'], 'Account created successfully. Please login.')
        
        created_user = User.get_by_username('newemp')
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.role, 'employee')
        self.assertTrue(created_user.check_password('newpassword123'))

    def test_signup_username_already_exists(self):
        # emp1 is created in setUp
        response = self.client.post('/signup', json={
            'username': 'emp1', # This username already exists
            'password': 'anotherpassword'
        })
        self.assertEqual(response.status_code, 409, msg=response.get_json())
        self.assertEqual(response.json['error'], 'Username already exists')

    def test_signup_password_too_short(self):
        response = self.client.post('/signup', json={
            'username': 'shortpassuser',
            'password': 'short' # Less than 8 characters
        })
        self.assertEqual(response.status_code, 400, msg=response.get_json())
        self.assertEqual(response.json['error'], 'Password must be at least 8 characters long')

    def test_signup_missing_username(self):
        response = self.client.post('/signup', json={
            'password': 'validpassword123'
            # Username missing
        })
        self.assertEqual(response.status_code, 400, msg=response.get_json())
        self.assertEqual(response.json['error'], 'Username and password are required')

    def test_signup_missing_password(self):
        response = self.client.post('/signup', json={
            'username': 'nopassuser'
            # Password missing
        })
        self.assertEqual(response.status_code, 400, msg=response.get_json())
        self.assertEqual(response.json['error'], 'Username and password are required')

    def test_signup_invalid_json(self):
        response = self.client.post('/signup', data="not json", content_type='application/json')
        self.assertEqual(response.status_code, 400, msg=response.get_data(as_text=True))
        
        json_response = response.get_json()
        self.assertIsNotNone(json_response, "Response should be JSON for a malformed JSON request to /signup.")
        self.assertIn('error', json_response)
        # Check against the updated error message from the route
        self.assertEqual(json_response['error'], 'Invalid JSON payload or malformed JSON')


class TestExpenseRoutes(BaseTestCase):
    def setUp(self): # Override BaseTestCase.setUp to add specific user for expense tests
        super().setUp() # This now calls the patched setUp from BaseTestCase
        self.employee_token = self.login_as('emp1', 'emp1pass')
        # Fetch user from mongomock via the model's method
        self.employee_user = User.get_by_username('emp1')
        self.assertIsNotNone(self.employee_user, "Employee 'emp1' should exist after setup.")


    def test_submit_expense_success(self):
        data = {
            'amount': '100.50',
            'currency': 'USD',
            'date': '2024-01-15',
            'vendor': 'Test Vendor',
            'description': 'Test expense description'
        }
        receipt_content = b"This is a dummy receipt."
        receipt = (BytesIO(receipt_content), 'receipt.pdf') # Changed to .pdf
        data['receipt'] = receipt

        response = self.client.post('/expenses',
                                     headers={'Authorization': f'Bearer {self.employee_token}'},
                                     data=data,
                                     content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 201, msg=response.get_data(as_text=True))
        json_response = response.get_json()
        self.assertEqual(json_response['expense']['amount'], 100.50)
        self.assertEqual(json_response['expense']['vendor'], 'Test Vendor')
        self.assertIn('ocr_data', json_response) 
        self.assertTrue(json_response['expense']['receipt_url'].endswith(f'{SIMULATED_CLOUD_FOLDER}/receipt.pdf')) # Changed to .pdf
        
        # Check if file was "uploaded"
        # self.app.config['UPLOAD_FOLDER'] is the temp_upload_folder (absolute path)
        expected_receipt_path = os.path.join(self.app.config['UPLOAD_FOLDER'], SIMULATED_CLOUD_FOLDER, 'receipt.pdf') # Changed to .pdf
        self.assertTrue(os.path.exists(expected_receipt_path))


    def test_submit_expense_missing_data(self):
        data = {'amount': '50'} 
        receipt = (BytesIO(b"dummy"), 'r.pdf') # Changed to .pdf for consistency
        data['receipt'] = receipt
        response = self.client.post('/expenses',
                                     headers={'Authorization': f'Bearer {self.employee_token}'},
                                     data=data,
                                     content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)

    def test_submit_expense_invalid_file_type(self):
        data = {
            'amount': '20', 'date': '2024-01-16', 'vendor': 'Bad File Co'
        }
        receipt = (BytesIO(b"dummy script"), 'receipt.exe') 
        data['receipt'] = receipt
        response = self.client.post('/expenses',
                                     headers={'Authorization': f'Bearer {self.employee_token}'},
                                     data=data,
                                     content_type='multipart/form-data')
        self.assertEqual(response.status_code, 400)
        self.assertIn("File type not allowed", response.get_json()['error'])


    def test_get_expenses_for_employee(self):
        data = {'amount': '123.45', 'date': '2024-01-17', 'vendor': 'My Vendor', 
                'receipt': (BytesIO(b"receipt data"), 'my_receipt.pdf')}
        submit_response = self.client.post('/expenses',
                                     headers={'Authorization': f'Bearer {self.employee_token}'},
                                     data=data, content_type='multipart/form-data')
        self.assertEqual(submit_response.status_code, 201, msg=submit_response.get_data(as_text=True))
        # The route returns 'id' not '_id' in the JSON response for an expense
        submitted_expense_id = submit_response.get_json()['expense']['id']

        response = self.client.get('/expenses', headers={'Authorization': f'Bearer {self.employee_token}'})
        self.assertEqual(response.status_code, 200)
        expenses_json = response.get_json()
        self.assertEqual(len(expenses_json), 1)
        # Verify using the ID from the submission response
        retrieved_expense = None
        for exp in expenses_json:
            # The GET /expenses route also returns 'id' not '_id'
            if exp['id'] == submitted_expense_id:
                retrieved_expense = exp
                break
        self.assertIsNotNone(retrieved_expense, "Submitted expense not found in GET response.")
        self.assertEqual(retrieved_expense['amount'], 123.45)
        self.assertEqual(retrieved_expense['vendor'], 'My Vendor')
        self.assertTrue(retrieved_expense['receipt_url'].endswith(f'{SIMULATED_CLOUD_FOLDER}/my_receipt.pdf'))

    def test_get_expenses_unauthorized(self):
        # Create emp2 if it doesn't exist. User.save() now uses mongomock.
        if not User.get_by_username("emp2"):
            Employee("emp2", "emp2pass").save()
        other_employee_token = self.login_as("emp2", "emp2pass")

        # emp1 submits an expense
        data_emp1 = {'amount': '10.00', 'date': '2024-01-18', 'vendor': 'Emp1 Vendor', 
                     'receipt': (BytesIO(b"receipt data for emp1"), 'emp1_receipt.png')}
        submit_response_emp1 = self.client.post('/expenses',
                                             headers={'Authorization': f'Bearer {self.employee_token}'},
                                             data=data_emp1, content_type='multipart/form-data')
        self.assertEqual(submit_response_emp1.status_code, 201, msg=submit_response_emp1.get_data(as_text=True))
        
        # emp2 tries to get expenses, should only see their own (none in this case)
        response_emp2_gets_expenses = self.client.get('/expenses', headers={'Authorization': f'Bearer {other_employee_token}'})
        self.assertEqual(response_emp2_gets_expenses.status_code, 200)
        self.assertEqual(len(response_emp2_gets_expenses.get_json()), 0, 
                         "emp2 should not see emp1's expenses.")

if __name__ == '__main__':
    unittest.main()
