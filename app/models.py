import uuid # Still used for default Expense ID if not loading from DB initially
from werkzeug.security import generate_password_hash, check_password_hash
from .database import get_db # For MongoDB access
from datetime import datetime, date # Ensure datetime is imported
from bson.objectid import ObjectId # For MongoDB ObjectIDs

# User, Employee, Admin classes and create_dummy_users function
# These are preserved as they are already MongoDB-enabled.

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
            'username': self.username, 
            'password_hash': self.password_hash,
            'role': self.role
        }
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
            if role == 'admin':
                return Admin(username=user_doc['_id'], password=user_doc['password_hash'], _is_from_db=True)
            elif role == 'employee':
                return Employee(username=user_doc['_id'], password=user_doc['password_hash'], _is_from_db=True)
            return cls(username=user_doc['_id'], password=user_doc['password_hash'], role=role, _is_from_db=True)
        return None

class Employee(User):
    def __init__(self, username, password, _is_from_db=False):
        super().__init__(username, password, role="employee", _is_from_db=_is_from_db)

class Admin(User):
    def __init__(self, username, password, _is_from_db=False):
        super().__init__(username, password, role="admin", _is_from_db=_is_from_db)

def create_dummy_users():
    if not User.get_by_username("emp1"):
        emp = Employee(username="emp1", password="emp1pass")
        emp.save()
    if not User.get_by_username("admin1"):
        adm = Admin(username="admin1", password="admin1pass")
        adm.save()

# EXPENSES_DB list removed.

# Expense class (to replace existing one in app/models.py)
class Expense:
    def __init__(self, user_id, amount, currency, date_str, vendor, description, 
                 receipt_cloud_path, status="pending", created_at=None, _id=None):
        # If _id is provided, it's from DB (ObjectId)
        # Otherwise, when creating new, _id will be set by MongoDB on insert
        self._id = ObjectId(_id) if _id else None 
        
        self.user_id = user_id # Should reference User's _id (which is username)
        self.amount = float(amount)
        self.currency = currency
        
        try:
            # Attempt to parse date_str, assuming YYYY-MM-DD or datetime object
            if isinstance(date_str, datetime):
                self.date = date_str
            elif isinstance(date_str, date):
                self.date = datetime.combine(date_str, datetime.min.time())
            else: # Assuming string
                self.date = datetime.fromisoformat(date_str.replace('Z', '+00:00')) # Handle ISO format, ensure UTC if Z present
        except ValueError:
            # Fallback for simple YYYY-MM-DD if fromisoformat fails directly due to no T part
            try:
                self.date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                raise ValueError("Invalid date format for Expense. Use YYYY-MM-DD or ISO datetime string.")

        self.vendor = vendor
        self.description = description
        self.receipt_cloud_path = receipt_cloud_path
        self.status = status
        self.created_at = created_at if created_at else datetime.utcnow()

    def save(self):
        expenses_collection = get_db().expenses
        expense_doc = {
            'user_id': self.user_id,
            'amount': self.amount,
            'currency': self.currency,
            'date': self.date, # Store as BSON date (datetime object)
            'vendor': self.vendor,
            'description': self.description,
            'receipt_cloud_path': self.receipt_cloud_path,
            'status': self.status,
            'created_at': self.created_at
        }
        if self._id: # If expense has an _id, it's an update
            expenses_collection.update_one({'_id': self._id}, {'$set': expense_doc})
        else: # New expense, insert it
            result = expenses_collection.insert_one(expense_doc)
            self._id = result.inserted_id # Set the _id from MongoDB

    @classmethod
    def from_document(cls, doc):
        """Helper classmethod to create an Expense instance from a MongoDB document."""
        if not doc:
            return None
        return cls(
            _id=doc.get('_id'), # Pass ObjectId directly
            user_id=doc.get('user_id'),
            amount=doc.get('amount'),
            currency=doc.get('currency'),
            date_str=doc.get('date'), # MongoDB returns datetime object for BSON dates
            vendor=doc.get('vendor'),
            description=doc.get('description'),
            receipt_cloud_path=doc.get('receipt_cloud_path'),
            status=doc.get('status'),
            created_at=doc.get('created_at')
        )

    @classmethod
    def get_by_id(cls, expense_id_str):
        try:
            obj_id = ObjectId(expense_id_str)
        except Exception: # Invalid ObjectId format
            return None
        expenses_collection = get_db().expenses
        expense_doc = expenses_collection.find_one({'_id': obj_id})
        return cls.from_document(expense_doc)

    @classmethod
    def get_by_user_id(cls, user_id):
        expenses_collection = get_db().expenses
        # Sort by date descending, most recent first
        expense_docs = expenses_collection.find({'user_id': user_id}).sort('date', -1) 
        return [cls.from_document(doc) for doc in expense_docs]

    def get_receipt_url(self):
        from .storage_services import get_file_url_from_cloud 
        return get_file_url_from_cloud(self.receipt_cloud_path)

# Call to create_dummy_users() is in app/__init__.py and should not be here.
