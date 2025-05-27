from flask import Flask
from flask_cors import CORS 
import os
from . import database 

def create_app():
    app = Flask(__name__)
    CORS(app) 
    
    app.config.from_object('config.Config') 

    project_root = os.path.dirname(app.root_path) 
    upload_dir_path = os.path.join(project_root, app.config['UPLOAD_FOLDER'])
    
    if not os.path.exists(upload_dir_path):
        os.makedirs(upload_dir_path)

    database.init_app(app) 

    with app.app_context():
        # Import and register Blueprints
        from . import routes 
        app.register_blueprint(routes.bp) 

        from . import models 
        models.create_dummy_users() # Added/Uncommented to call the function

    return app
