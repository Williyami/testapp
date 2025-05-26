import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    DEBUG = os.environ.get('FLASK_DEBUG') or True
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    # Add other configurations like database URI later
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or         #    'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    # SQLALCHEMY_TRACK_MODIFICATIONS = False
