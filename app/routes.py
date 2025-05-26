from flask import Blueprint, request, jsonify, current_app # Keep current_app for logger and config
from .models import User, SESSIONS_DB, Expense, EXPENSES_DB 
from werkzeug.utils import secure_filename
import os
import uuid

from .ocr_services import extract_text_from_receipt
from .storage_services import upload_file_to_cloud, delete_file_from_cloud, SIMULATED_CLOUD_FOLDER

# Define a Blueprint
bp = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/health') # Changed from @current_app.route
def health_check():
    return jsonify(status="UP", message="Expense platform is running!")

@bp.route('/login', methods=['POST']) # Changed
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

@bp.route('/logout', methods=['POST']) # Changed
def logout():
    token = request.headers.get('Authorization') 
    if token:
        token = token.replace("Bearer ", "")
        if token in SESSIONS_DB:
            del SESSIONS_DB[token]
    return jsonify({"message": "Logout successful (mocked)"}), 200

@bp.route('/me', methods=['GET']) # Changed
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

@bp.route('/expenses', methods=['POST']) # Changed
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
        current_app.logger.info(f"OCR Results for {filename}: {ocr_results}") # current_app for logger
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

@bp.route('/expenses', methods=['GET']) # Changed
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
