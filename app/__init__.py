from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config') 

    project_root = os.path.dirname(app.root_path) 
    upload_dir_path = os.path.join(project_root, app.config['UPLOAD_FOLDER'])
    
    if not os.path.exists(upload_dir_path):
        os.makedirs(upload_dir_path)

    with app.app_context():
        # Import and register Blueprints
        from . import routes # This now contains the blueprint 'bp'
        app.register_blueprint(routes.bp) # Register the blueprint

        from . import models 
        # models.create_dummy_users() is called in models.py

    return app
