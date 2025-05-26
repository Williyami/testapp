print("DEBUG: LOADING app/routes.py - DEBUG VERSION FOR SIGNUP ROUTING CHECK") 
from flask import Blueprint, request, jsonify, current_app 
from .models import User, Employee, SESSIONS_DB, Expense, EXPENSES_DB
from werkzeug.utils import secure_filename
import os
import uuid

from .ocr_services import extract_text_from_receipt
from .storage_services import upload_file_to_cloud, delete_file_from_cloud, SIMULATED_CLOUD_FOLDER

# Define a Blueprint
bp = Blueprint('main', __name__)

# --- Temporary Debug Routes ---
# Existing /signup route(s) will be removed and replaced by combined_signup_route below

@bp.route('/show-routes-debug')
def show_routes_debug():
    import urllib.parse 
    output = []
    rules = sorted(current_app.url_map.iter_rules(), key=lambda rule: rule.rule)
    for rule in rules:
        options = {}
        for arg in rule.arguments:
            options[arg] = "[{0}]".format(arg)
        
        methods = ','.join(sorted(rule.methods))
        url = urllib.parse.unquote(rule.rule) 
        line = "{:50s} {:30s} {}".format(url, methods, options)
        output.append(line)
    
    html_output = "<html><head><title>Registered Routes</title></head><body>"
    html_output += "<h1>Registered Routes</h1><pre>"
    html_output += "\n".join(output) 
    html_output += "</pre></body></html>"
    return html_output
# --- End Temporary Debug Routes ---

# --- New Combined Signup Route ---
# This new combined function should be the ONLY @bp.route('/signup',...)
# in app/routes.py after this operation.

@bp.route('/signup', methods=['GET', 'POST'])
def combined_signup_route(): # Renamed function slightly to ensure it's "new"
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        if User.get_by_username(username): # Assuming User is imported
            return jsonify({"error": "Username already exists"}), 409

        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400

        try:
            # Assuming Employee is imported
            new_user = Employee(username=username, password=password)
            new_user.save()
        except Exception as e:
            current_app.logger.error(f"Error during user creation: {e}") # Assuming current_app
            return jsonify({"error": "An unexpected error occurred during account creation."}), 500
        
        return jsonify({"message": "Account created successfully. Please login."}), 201
    
    elif request.method == 'GET':
        # This is the debug GET response
        return jsonify({"message": "GET /signup is reachable (debug - combined route v2)"}), 200
    
    # Fallback for any other methods (though Flask usually handles this with a 405)
    return jsonify({"error": "Method not explicitly handled"}), 405
# --- End New Combined Signup Route ---


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
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
        session_token = str(uuid.uuid4())
        SESSIONS_DB[session_token] = user.username 
        return jsonify({
            "message": "Login successful",
            "token": session_token,
            "user": {"username": user.username, "role": user.role, "id": user.id}
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

@bp.route('/logout', methods=['POST']) 
def logout():
    token = request.headers.get('Authorization') 
    if token:
        token = token.replace("Bearer ", "")
        if token in SESSIONS_DB:
            del SESSIONS_DB[token]
    return jsonify({"message": "Logout successful (mocked)"}), 200

@bp.route('/me', methods=['GET']) 
def me():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"error": "Missing token"}), 401
    
    token = token.replace("Bearer ", "")
    username = SESSIONS_DB.get(token)
    if not username:
        return jsonify({"error": "Invalid or expired token"}), 401
        
    user = User.get_by_username(username)
    if user:
        return jsonify({
            "username": user.username,
            "role": user.role,
            "id": user.id
        }), 200
    return jsonify({"error": "User not found for token"}), 404

@bp.route('/expenses', methods=['POST']) 
def submit_expense():
    token = request.headers.get('Authorization')
    if not token: return jsonify({"error": "Missing token"}), 401
    token = token.replace("Bearer ", "")
    username = SESSIONS_DB.get(token)
    if not username: return jsonify({"error": "Invalid or expired token"}), 401
    user = User.get_by_username(username)
    if not user or user.role != "employee": return jsonify({"error": "Unauthorized"}), 403

    if 'receipt' not in request.files: return jsonify({"error": "No receipt file part"}), 400
    file = request.files['receipt']
    if file.filename == '': return jsonify({"error": "No selected file"}), 400
    if not allowed_file(file.filename): return jsonify({"error": "File type not allowed"}), 400
            
    try:
        amount = float(request.form.get('amount'))
        currency = request.form.get('currency', 'USD')
        date_str = request.form.get('date') 
        vendor = request.form.get('vendor')
        description = request.form.get('description', '')
    except (TypeError, ValueError) as e:
         return jsonify({"error": f"Invalid form data: {e}"}), 400

    if not all([amount is not None, date_str, vendor]):
        return jsonify({"error": "Missing required expense data: amount, date, vendor"}), 400

    filename = secure_filename(file.filename)
    
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
        cloud_receipt_path = upload_file_to_cloud(file, filename, user.id)
        
        new_expense = Expense(
            user_id=user.id,
            amount=amount,
            currency=currency,
            date=date_str,
            vendor=vendor,
            description=description,
            receipt_cloud_path=cloud_receipt_path
        )
        new_expense.save()

    except ValueError as e:
        if cloud_receipt_path:
            delete_file_from_cloud(cloud_receipt_path)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error during expense submission: {str(e)}")
        if cloud_receipt_path:
            delete_file_from_cloud(cloud_receipt_path)
        return jsonify({"error": f"Could not process expense: {str(e)}"}), 500
    finally:
        if os.path.exists(temp_receipt_path_for_ocr):
            os.remove(temp_receipt_path_for_ocr)
        if os.path.exists(temp_ocr_dir) and not os.listdir(temp_ocr_dir):
            try:
                os.rmdir(temp_ocr_dir)
            except OSError:
                current_app.logger.warning(f"Could not remove temp_ocr_dir: {temp_ocr_dir}, possibly not empty.")

    return jsonify({
        "message": "Expense submitted successfully",
        "expense": {
            "id": new_expense.id,
            "user_id": new_expense.user_id,
            "amount": new_expense.amount,
            "currency": new_expense.currency,
            "date": new_expense.date.isoformat(),
            "vendor": new_expense.vendor,
            "description": new_expense.description,
            "receipt_url": new_expense.get_receipt_url(),
            "status": new_expense.status,
            "created_at": new_expense.created_at.isoformat()
        },
        "ocr_data": ocr_results
    }), 201

@bp.route('/expenses', methods=['GET']) 
def get_expenses():
    token = request.headers.get('Authorization')
    if not token: return jsonify({"error": "Missing token"}), 401
    token = token.replace("Bearer ", "")
    username = SESSIONS_DB.get(token)
    if not username: return jsonify({"error": "Invalid or expired token"}), 401
    user = User.get_by_username(username)
    if not user: return jsonify({"error": "User not found"}), 404
    
    user_expenses = Expense.get_by_user_id(user.id)
    return jsonify([
        {
            "id": exp.id,
            "user_id": exp.user_id,
            "amount": exp.amount,
            "currency": exp.currency,
            "date": exp.date.isoformat(),
            "vendor": exp.vendor,
            "description": exp.description,
            "receipt_url": exp.get_receipt_url(),
            "status": exp.status,
            "created_at": exp.created_at.isoformat()
        } for exp in user_expenses
    ]), 200

# Removed old POST-only signup function. The combined_signup_route handles this now.
