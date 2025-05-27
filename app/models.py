import uuid # Keep for Expense IDs for now, not User IDs
from werkzeug.security import generate_password_hash, check_password_hash
from .database import get_db # For MongoDB access
from datetime import datetime, date # Keep for Expense model, date used for BSON

# User, Employee, Admin classes and create_dummy_users function
# (to replace existing ones in app/models.py)

class User:
    def __init__(self, username, password, role="employee", _is_from_db=False):
        self.username = username  # This will be used as _id in MongoDB
        if _is_from_db:
            self.password_hash = password  # In this case, 'password' is the hash from DB
        else:
            if not password: # Ensure password is not None or empty before hashing
                raise ValueError("Password cannot be empty.")
            self.password_hash = generate_password_hash(password)
        self.role = role

    def save(self):
        users_collection = get_db().users
        user_doc = {
            # '_id': self.username, # MongoDB uses _id for the primary key
            'username': self.username, # Store username explicitly in the doc body as well
            'password_hash': self.password_hash,
            'role': self.role
        }
        # Use self.username as the value for the _id field for querying and upserting
        users_collection.update_one({'_id': self.username}, {'$set': user_doc}, upsert=True)

    def check_password(self, password):
        if not password or not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_by_username(cls, username):
        users_collection = get_db().users
        user_doc = users_collection.find_one({'_id': username})
        if user_doc:
            role = user_doc.get('role')
            # Instantiate the correct subclass based on role
            if role == 'admin':
                return Admin(username=user_doc['_id'], password=user_doc['password_hash'], _is_from_db=True)
            elif role == 'employee':
                return Employee(username=user_doc['_id'], password=user_doc['password_hash'], _is_from_db=True)
            # Fallback if role is different or not set, create base User instance
            # This case should ideally not happen if roles are managed strictly
            return cls(username=user_doc['_id'], password=user_doc['password_hash'], role=role, _is_from_db=True)
        return None

class Employee(User):
    def __init__(self, username, password, _is_from_db=False):
        super().__init__(username, password, role="employee", _is_from_db=_is_from_db)
        # Employee-specific attributes can be added here later

class Admin(User):
    def __init__(self, username, password, _is_from_db=False):
        super().__init__(username, password, role="admin", _is_from_db=_is_from_db)
        # Admin-specific attributes can be added here later

def create_dummy_users():
    # Ensure this function is called within an app context where get_db() can access current_app
    # Check if users exist before attempting to create and save them
    if not User.get_by_username("emp1"):
        emp = Employee(username="emp1", password="emp1pass")
        emp.save()
        # print("Created dummy employee 'emp1'") # Optional: for debugging
    
    if not User.get_by_username("admin1"):
        adm = Admin(username="admin1", password="admin1pass")
        adm.save()
        # print("Created dummy admin 'admin1'") # Optional: for debugging

# Keep the Expense model and EXPENSES_DB (or its MongoDB equivalent plan) for later refactoring.
# For now, this subtask only focuses on User, Employee, Admin, and create_dummy_users.
# The existing Expense model and EXPENSES_DB list will be refactored in a separate step.
EXPENSES_DB = [] 

class Expense:
    def __init__(self, user_id, amount, currency, date_str, vendor, description, receipt_cloud_path): # Changed 'date' to 'date_str' to match type
        self.id = str(uuid.uuid4()) 
        self.user_id = user_id 
        self.amount = amount
        self.currency = currency
        try:
            self.date = date.fromisoformat(date_str) # Use imported 'date'
        except ValueError:
            raise ValueError("Invalid date format for expense. Use YYYY-MM-DD.")
        self.vendor = vendor
        self.description = description
        self.receipt_cloud_path = receipt_cloud_path
        self.status = "pending"
        self.created_at = datetime.utcnow() # Use imported 'datetime'

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

# create_dummy_users() # Call removed from here, will be called from app/__init__.py
