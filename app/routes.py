print("DEBUG: LOADING app/routes.py - DEBUG VERSION FOR SIGNUP ROUTING CHECK") 
from flask import Blueprint, request, jsonify, current_app 
from .models import User, Employee, Expense # EXPENSES_DB removed
from .database import get_db 
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime, timedelta 

from .ocr_services import extract_text_from_receipt
from .storage_services import upload_file_to_cloud, delete_file_from_cloud, SIMULATED_CLOUD_FOLDER

# Define a Blueprint
bp = Blueprint('main', __name__)

# Debug print statement removed.
# Debug routes /show-routes-debug and GET /signup removed.

@bp.route('/signup', methods=['POST']) 
def combined_signup_route(): 
    data = request.get_json(silent=True) # Use silent=True to prevent raising BadRequest on parse error
    if not data:
        # This will now catch both empty payload and malformed JSON
        return jsonify({"error": "Invalid JSON payload or malformed JSON"}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if User.get_by_username(username): 
        return jsonify({"error": "Username already exists"}), 409

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400

    try:
        new_user = Employee(username=username, password=password)
        new_user.save()
    except Exception as e:
        current_app.logger.error(f"Error during user creation: {e}") 
        return jsonify({"error": "An unexpected error occurred during account creation."}), 500
    
    return jsonify({"message": "Account created successfully. Please login."}), 201
# --- End Signup Route ---


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'} # This should be present

def allowed_file(filename): # This should be present
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/health') 
def health_check():
    return jsonify(status="UP", message="Expense platform is running!")

@bp.route('/login', methods=['POST']) 
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = User.get_by_username(username)
    if user and user.check_password(password):
        sessions_collection = get_db().sessions 
        session_token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(days=1) 
        session_doc = {
            '_id': session_token,
            'username': user.username, 
            'expires_at': expires_at
        }
        sessions_collection.update_one({'_id': session_token}, {'$set': session_doc}, upsert=True)
        
        return jsonify({
            "message": "Login successful",
            "token": session_token,
            "user": {"username": user.username, "role": user.role, "id": user.username} 
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

@bp.route('/logout', methods=['POST']) 
def logout():
    token = request.headers.get('Authorization') 
    if token:
        token = token.replace("Bearer ", "")
        if token: 
            sessions_collection = get_db().sessions
            sessions_collection.delete_one({'_id': token})
    return jsonify({"message": "Logout successful"}), 200

@bp.route('/me', methods=['GET']) 
def me():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Missing token"}), 401
    
    token = token.replace("Bearer ", "")
    if not token: 
        return jsonify({"error": "Invalid token format"}), 401

    sessions_collection = get_db().sessions
    session_doc = sessions_collection.find_one({'_id': token})

    if session_doc:
        if session_doc.get('expires_at') and session_doc['expires_at'] < datetime.utcnow():
            sessions_collection.delete_one({'_id': token}) 
            return jsonify({"error": "Session expired. Please login again."}), 401

        username_from_session = session_doc.get('username')
        if username_from_session:
            user = User.get_by_username(username_from_session) 
            if user:
                return jsonify({
                    "username": user.username,
                    "role": user.role,
                    "id": user.username 
                }), 200
            return jsonify({"error": "User associated with session not found"}), 404 
        
    return jsonify({"error": "Invalid or expired token"}), 401 

# In app/routes.py, part of the 'bp' Blueprint
@bp.route('/expenses', methods=['POST'])
def submit_expense():
    # Token and user authentication (remains largely the same, relies on MongoDB sessions now)
    token = request.headers.get('Authorization')
    if not token: return jsonify({"error": "Missing token"}), 401
    token = token.replace("Bearer ", "")
    if not token: return jsonify({"error": "Invalid token format"}), 401

    sessions_collection = get_db().sessions # Assumes get_db() is imported
    session_doc = sessions_collection.find_one({'_id': token})

    if not session_doc: return jsonify({"error": "Invalid or expired token"}), 401
    if session_doc.get('expires_at') and session_doc['expires_at'] < datetime.utcnow(): # Assumes datetime imported
        sessions_collection.delete_one({'_id': token})
        return jsonify({"error": "Session expired. Please login again."}), 401
    
    username_from_session = session_doc.get('username')
    if not username_from_session: return jsonify({"error": "Session is invalid (no username)"}), 401
    
    user = User.get_by_username(username_from_session) # Fetches from MongoDB
    if not user or user.role != "employee": 
        return jsonify({"error": "Unauthorized or not an employee"}), 403

    # File handling for receipt (remains largely the same)
    if 'receipt' not in request.files: return jsonify({"error": "No receipt file part"}), 400
    file = request.files['receipt']
    if file.filename == '': return jsonify({"error": "No selected file"}), 400
    # Ensure allowed_file function is defined or imported if used here
    # def allowed_file(filename): return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    if not allowed_file(file.filename): return jsonify({"error": "File type not allowed"}), 400 # Make sure ALLOWED_EXTENSIONS is defined
        
    # Form data extraction
    try:
        amount = float(request.form.get('amount'))
        currency = request.form.get('currency', 'USD')
        date_str = request.form.get('date') # Expecting YYYY-MM-DD string from form
        vendor = request.form.get('vendor')
        description = request.form.get('description', '')
    except (TypeError, ValueError) as e:
         return jsonify({"error": f"Invalid form data: {e}"}), 400

    if not all([amount is not None, date_str, vendor]): # amount can be 0.0
        return jsonify({"error": "Missing required expense data: amount, date, vendor"}), 400

    filename = secure_filename(file.filename)
    
    # Path setup for temp OCR file (remains largely the same)
    project_root = os.path.dirname(current_app.root_path)
    base_upload_folder = current_app.config['UPLOAD_FOLDER']
    temp_ocr_dir = os.path.join(project_root, base_upload_folder, 'temp_for_ocr')
    if not os.path.exists(temp_ocr_dir):
        os.makedirs(temp_ocr_dir, exist_ok=True)
    temp_receipt_path_for_ocr = os.path.join(temp_ocr_dir, filename)

    cloud_receipt_path = None
    ocr_results = {}

    try:
        file.save(temp_receipt_path_for_ocr)
        ocr_results = extract_text_from_receipt(temp_receipt_path_for_ocr)
        current_app.logger.info(f"OCR Results for {filename}: {ocr_results}")
        file.seek(0) 
        cloud_receipt_path = upload_file_to_cloud(file, filename, user.username) # Pass user.username as user_id
        
        # Create Expense object (model now handles date_str to datetime conversion)
        new_expense = Expense(
            user_id=user.username, # Link expense to user's username (which is user._id)
            amount=amount,
            currency=currency,
            date_str=date_str, # Pass the string from form
            vendor=vendor,
            description=description,
            receipt_cloud_path=cloud_receipt_path
            # status defaults to "pending", created_at defaults to now in model
        )
        new_expense.save() # This now saves to MongoDB and sets new_expense._id

    except ValueError as e: # For date conversion or other model validation errors
        if cloud_receipt_path: delete_file_from_cloud(cloud_receipt_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error during expense submission: {str(e)}")
        if cloud_receipt_path: delete_file_from_cloud(cloud_receipt_path)
        return jsonify({"error": f"Could not process expense: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_receipt_path_for_ocr): os.remove(temp_receipt_path_for_ocr)
        if os.path.exists(temp_ocr_dir) and not os.listdir(temp_ocr_dir):
            try: os.rmdir(temp_ocr_dir)
            except OSError: current_app.logger.warning(f"Could not remove temp_ocr_dir: {temp_ocr_dir}")
    
    # Return MongoDB ObjectId as string for the ID
    return jsonify({
        "message": "Expense submitted successfully",
        "expense": {
            "id": str(new_expense._id), # Convert ObjectId to string
            "user_id": new_expense.user_id,
            "amount": new_expense.amount,
            "currency": new_expense.currency,
            "date": new_expense.date.isoformat(), # Model stores date as datetime
            "vendor": new_expense.vendor,
            "description": new_expense.description,
            "receipt_url": new_expense.get_receipt_url(),
            "status": new_expense.status,
            "created_at": new_expense.created_at.isoformat()
        },
        "ocr_data": ocr_results
    }), 201

# In app/routes.py, part of the 'bp' Blueprint
@bp.route('/expenses', methods=['GET'])
def get_expenses():
    # Token and user authentication (similar to POST /expenses, uses MongoDB sessions)
    token = request.headers.get('Authorization')
    if not token: return jsonify({"error": "Missing token"}), 401
    token = token.replace("Bearer ", "")
    if not token: return jsonify({"error": "Invalid token format"}), 401

    sessions_collection = get_db().sessions
    session_doc = sessions_collection.find_one({'_id': token})

    if not session_doc: return jsonify({"error": "Invalid or expired token"}), 401
    if session_doc.get('expires_at') and session_doc['expires_at'] < datetime.utcnow():
        sessions_collection.delete_one({'_id': token})
        return jsonify({"error": "Session expired. Please login again."}), 401

    username_from_session = session_doc.get('username')
    if not username_from_session: return jsonify({"error": "Session is invalid (no username)"}), 401
        
    user = User.get_by_username(username_from_session) # Fetches from MongoDB
    if not user: return jsonify({"error": "User not found for session"}), 404
    
    # Fetch expenses for this user from MongoDB via model method
    user_expenses = Expense.get_by_user_id(user.username) # Pass username as user_id
    
    return jsonify([
        {
            "id": str(exp._id), # Convert ObjectId to string
            "user_id": exp.user_id,
            "amount": exp.amount,
            "currency": exp.currency,
            "date": exp.date.isoformat(), # Model stores date as datetime
            "vendor": exp.vendor,
            "description": exp.description,
            "receipt_url": exp.get_receipt_url(),
            "status": exp.status,
            "created_at": exp.created_at.isoformat()
        } for exp in user_expenses
    ]), 200

# Note: The old POST-only signup function was part of the combined_signup_route,
# which is now correctly defined as POST-only.
# The temporary GET handler for /signup was also part of combined_signup_route and is now removed.
# The /show-routes-debug function was also removed.
