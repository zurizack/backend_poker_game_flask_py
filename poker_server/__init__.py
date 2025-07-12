# poker_server/__init__.py
from typing import Optional, Dict, Any, List
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
import logging # Import logging
import os
import sys


# Initialize SQLAlchemy database object (without app context here)
db = SQLAlchemy()

# Initialize Flask-Login manager (without app context here)
login_manager = LoginManager()

allowed_origins = os.getenv('CORS_ALLOWED_ORIGIN', 'http://localhost:3000')

# Initialize SocketIO (without app context here)
socketio = SocketIO()
# socketio = SocketIO(cors_allowed_origins=allowed_origins, manage_session=False, async_mode='gevent')

# --- Import GameManager and DBManager ---
# Ensure these paths are correct!
from .sql_services.db_manager import DBManager
from .game.engine.game_manager_oop import GameManager 

# --- Global variable to store GameManager instance ---
# This will be the single instance of GameManager accessible to all parts of the application.
game_manager_instance: Optional[GameManager] = None
db_manager_instance: Optional[DBManager] = None # Added global variable for DBManager as well


def create_app():
    """
    Application factory function:
    - Creates a Flask app instance
    - Loads configuration from settings.py
    - Initializes extensions (SQLAlchemy, LoginManager, SocketIO) with the app
    - Creates all database tables within the application context
    - Initializes GameManager and DBManager
    - Registers authentication and game blueprints
    - Returns the configured app instance
    """
    app = Flask(__name__)

    app.config.from_pyfile('config/settings.py')  # Loads configuration from an external file

    CORS(app, supports_credentials=True, origins=allowed_origins)

    # Bind SQLAlchemy and LoginManager instances to this app
    db.init_app(app)
    login_manager.init_app(app)

    socketio.init_app(app, cors_allowed_origins=allowed_origins, manage_session=False, async_mode='gevent')
    from .models.user import User
    from .models.poker_table import PokerTable

    # --- הגדרת לוגינג ---
    # הגדר את רמת הלוגינג הבסיסית ל-INFO ושלח פלט ל-sys.stdout
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    # וודא גם שלוגר האפליקציה של Flask מוגדר לרמת INFO
    app.logger.setLevel(logging.INFO)
    app.logger.info("Flask app logger initialized to INFO level.")

    # --- Create Database Tables ---
    with app.app_context():
        db.create_all()
        logging.info("Database tables created/updated successfully.")

        logging.info("Attempting to test database table existence by fetching a user...")
        try:
            first_user = User.query.first()
            if first_user:
                logging.info(f"Test fetch successful: Found existing user (ID: {first_user.id}). Tables exist and contain data.")
            else:
                logging.info("Test fetch successful: No existing users found. Tables exist but are empty.")
        except Exception as e:
            logging.error(f"Error during test fetch from User table: {e}")
            print(f"CRITICAL ERROR: Test fetch failed from User table: { {e} }", file=sys.stderr)
            logging.error("This likely means the database tables were NOT created successfully.")

        # --- Initialize DBManager and GameManager ---
        # We will use the global variables
        global db_manager_instance 
        global game_manager_instance

        # ✅ Step 1: Create an instance of DBManager and pass the Flask-SQLAlchemy db object
        db_manager_instance = DBManager(db) 
        # Can store it on the app object for convenient future access
        app.db_manager = db_manager_instance 
        logging.info("DBManager initialized successfully.") # Log for DBManager

        # ✅ Step 2: Create an instance of GameManager and pass the DBManager instance we created
        game_manager_instance = GameManager(db_manager_instance) 
        # Can store it on the app object for convenient future access
        app.game_manager = game_manager_instance 
        logging.info("GameManager initialized successfully within the application context.") # Log for GameManager


    # --- Configure Flask-Login user loader ---
    @login_manager.user_loader
    def load_user(user_id):
        """
        Flask-Login user loader callback.
        Given a user ID (as a string), returns the User object or None.
        This is used to reload the user from the session.
        """
        # Now we can use DBManager to load the user
        # Since db_manager_instance is global, we can access it directly.
        # Note: Flask-Login expects a User object, not a dictionary.
        # Therefore, we will need to fetch the full User object from the DB.
        # We will use db_manager_instance.get_user_by_id() (if it returns a full User object)
        # or User.query.get() directly if this is the Flask-Login context.
        # It's better to use DBManager for consistent access.
        if db_manager_instance: # Ensure db_manager_instance is already initialized
            return db_manager_instance.get_user_by_id(int(user_id))
        else:
            # If for some reason db_manager_instance is not yet initialized (edge case),
            # we will fall back to direct model access.
            from .models.user import User # Local import to prevent Circular Import
            return User.query.get(int(user_id))

    @app.after_request
    def log_set_cookie(response):
        # For debugging cookies, can replace with appropriate logging
        return response

    
    # --- Register Blueprints ---
    logging.info("Attempting to register blueprints...")
    from .auth.routes import auth_bp
    from .game import register_game_blueprints 

    app.register_blueprint(auth_bp)
    logging.info(f"Blueprint 'auth_bp' registered. URL prefix: {auth_bp.url_prefix}")

    register_game_blueprints(app) # Call the function that registers game Blueprints
    logging.info("Function 'register_game_blueprints' called.")

    # --- Initialize SocketIO Handlers and Emitters ---
    from .game.sockets.emitters_oop import PokerEmitters
    PokerEmitters.initialize(socketio) # Ensure PokerEmitters receives socketio

    from .game.sockets import register_socket_handlers
    register_socket_handlers(socketio) # Ensure register_socket_handlers receives socketio

    logging.info("App creation complete. Returning app instance.")
    return app
