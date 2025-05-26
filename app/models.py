import uuid
import datetime

# In-memory storage for users for now
USERS_DB = {} 
SESSIONS_DB = {} 

class User:
    def __init__(self, username, password_hash, role="employee"):
        self.id = str(uuid.uuid4())
        self.username = username
        self.password_hash = password_hash
        self.role = role

    def check_password(self, password):
        return self.password_hash == password

    @staticmethod
    def get_by_username(username):
        return USERS_DB.get(username)

    def save(self):
        USERS_DB[self.username] = self

class Employee(User):
    def __init__(self, username, password_hash):
        super().__init__(username, password_hash, role="employee")

class Admin(User):
    def __init__(self, username, password_hash):
        super().__init__(username, password_hash, role="admin")

def create_dummy_users():
    if not User.get_by_username("emp1"):
        Employee("emp1", "emp1pass").save()
    if not User.get_by_username("admin1"):
        Admin("admin1", "admin1pass").save()

EXPENSES_DB = [] 

class Expense:
    def __init__(self, user_id, amount, currency, date, vendor, description, receipt_cloud_path): # Changed
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
        self.receipt_cloud_path = receipt_cloud_path # Changed
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
        from .storage_services import get_file_url_from_cloud # Local import
        return get_file_url_from_cloud(self.receipt_cloud_path)

create_dummy_users()
