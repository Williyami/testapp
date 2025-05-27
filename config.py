import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    DEBUG = os.environ.get('FLASK_DEBUG') or True
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    
    # MongoDB Configuration
    # Fallback URI is intentionally a placeholder and should not connect to a real DB if committed.
    # The user's actual URI should be set as an environment variable MONGODB_URI.
    MONGODB_URI_FALLBACK = 'mongodb://localhost:27017/expense_app_default_db_placeholder'
    MONGODB_URI = os.environ.get('MONGODB_URI') or MONGODB_URI_FALLBACK

    # Based on user's URI appName=Revio1, but allow override.
    DATABASE_NAME_FALLBACK = 'Revio1' # Or a more generic 'expense_app_db'
    DATABASE_NAME = os.environ.get('DATABASE_NAME') or DATABASE_NAME_FALLBACK
    
    # Add other configurations like database URI later
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or         #    'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
