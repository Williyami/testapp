from pymongo import MongoClient
from flask import current_app, g # g is for application context global

# It's generally better to initialize the client once.
# However, if using Flask's app context, you might initialize it
# when the app is created or on first request.
# For simplicity here, we'll define a function that can be called.
# A more advanced setup might involve app factory pattern more deeply.

def get_mongo_client():
    """
    Returns an instance of MongoClient.
    Uses Flask's application context 'g' to store and reuse the client
    within the same context if already connected.
    """
    if 'mongo_client' not in g:
        try:
            mongo_uri = current_app.config['MONGODB_URI']
            # Add serverSelectionTimeoutMS to handle connection issues faster
            g.mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            # You can test the connection here if needed, e.g., by calling client.admin.command('ping')
            # g.mongo_client.admin.command('ping') # Optional: Test connection
            current_app.logger.info("MongoDB client initialized.")
        except Exception as e:
            current_app.logger.error(f"Failed to connect to MongoDB: {e}")
            raise # Re-raise the exception if connection fails
    return g.mongo_client

def get_db():
    """
    Returns a specific database instance from the MongoClient.
    """
    client = get_mongo_client()
    try:
        db_name = current_app.config['DATABASE_NAME']
        return client[db_name]
    except Exception as e:
        current_app.logger.error(f"Failed to get database '{current_app.config.get('DATABASE_NAME')}': {e}")
        raise

# Optional: Add a function to close the client when the app context tears down
def close_mongo_client(e=None):
    mongo_client = g.pop('mongo_client', None)
    if mongo_client is not None:
        mongo_client.close()
        current_app.logger.info("MongoDB client closed.")

# Function to be called from app factory in __init__.py
def init_app(app):
    app.teardown_appcontext(close_mongo_client)
    # You could also initialize a global client here if not using 'g'
    # For example:
    # global_mongo_client = MongoClient(app.config['MONGODB_URI'])
    # global_db = global_mongo_client[app.config['DATABASE_NAME']]
    # Then other modules import global_db from this file.
    # Using 'g' is generally cleaner for request contexts.
    pass # 'g' based approach doesn't need explicit init here other than teardown registration
