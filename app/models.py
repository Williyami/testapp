import uuid
import datetime
from werkzeug.security import generate_password_hash, check_password_hash # Added

# In-memory storage for users for now
USERS_DB = {} 
SESSIONS_DB = {} 

class User:
    def __init__(self, username, password, role="employee"): # Changed to password
        self.id = str(uuid.uuid4())
        self.username = username
        self.password_hash = generate_password_hash(password) # Hash password here
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password_hash, password) # Use check_password_hash

    @staticmethod
    def get_by_username(username):
        return USERS_DB.get(username)

    def save(self):
        USERS_DB[self.username] = self

class Employee(User):
    def __init__(self, username, password): # Changed to password
        super().__init__(username, password, role="employee") # Pass plain password to User.__init__

class Admin(User):
    def __init__(self, username, password): # Changed to password
        super().__init__(username, password, role="admin") # Pass plain password to User.__init__

def create_dummy_users():
    if not User.get_by_username("emp1"):
        Employee("emp1", "emp1pass").save() # Pass plain password
    if not User.get_by_username("admin1"):
        Admin("admin1", "admin1pass").save() # Pass plain password

EXPENSES_DB = [] 

class Expense:
    def __init__(self, user_id, amount, currency, date, vendor, description, receipt_cloud_path):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.amount = amount
        self.currency = currency
        try:
            self.date = datetime.date.fromisoformat(date)
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD.")
        self.vendor = vendor
        self.description = description
        self.receipt_cloud_path = receipt_cloud_path
        self.status = "pending"
        self.created_at = datetime.datetime.utcnow()

    def save(self):
        EXPENSES_DB.append(self)

    @staticmethod
    def get_by_id(expense_id):
        for expense in EXPENSES_DB:
            if expense.id == expense_id:
                return expense
        return None

    @staticmethod
    def get_by_user_id(user_id):
        return [expense for expense in EXPENSES_DB if expense.user_id == user_id]

    def get_receipt_url(self):
        from .storage_services import get_file_url_from_cloud 
        return get_file_url_from_cloud(self.receipt_cloud_path)

create_dummy_users()
