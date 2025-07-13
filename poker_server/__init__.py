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

# --- Import GameManager and DBManager ---
from .sql_services.db_manager import DBManager
from .game.engine.game_manager_oop import GameManager 

# --- Global variable to store GameManager instance ---
game_manager_instance: Optional[GameManager] = None
db_manager_instance: Optional[DBManager] = None


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

    # ✅ הגדרה קריטית: חיבור בלעדי לבסיס הנתונים המרוחק באמצעות משתנה הסביבה DATABASE_URL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') 
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # וודא שזה קיים

    CORS(app, supports_credentials=True, origins=allowed_origins)

    # Bind SQLAlchemy and LoginManager instances to this app
    db.init_app(app) 
    login_manager.init_app(app)

    socketio.init_app(app, cors_allowed_origins=allowed_origins, manage_session=False, async_mode='gevent')
    
    # --- הגדרת לוגינג (מוקדם ככל האפשר) ---
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Flask app logger initialized to INFO level.")

    # ✅ מיקום נכון לרישום ה-Blueprints!
    # זה חייב להיות כאן כדי שהם יירשמו לפני שהשרת מתחיל להאזין לבקשות.
    app.logger.info("Attempting to register blueprints (early stage)...") 
    from .auth.routes import auth_bp
    from .game import register_game_blueprints 

    app.register_blueprint(auth_bp)
    app.logger.info(f"Blueprint 'auth_bp' registered (early stage). URL prefix: {auth_bp.url_prefix}") 

    register_game_blueprints(app) # Call the function that registers game Blueprints
    app.logger.info("Function 'register_game_blueprints' called (early stage).") 

    # ייבוא מודלים (מוקדם מספיק, לפני db.create_all)
    from .models.user import User
    from .models.poker_table import PokerTable

    # --- Create Database Tables ---
    with app.app_context():
        db.create_all() 
        app.logger.info("Database tables created/updated successfully.") 

        app.logger.info("Attempting to test database table existence by fetching a user...") 
        try:
            first_user = User.query.first()
            if first_user:
                app.logger.info(f"Test fetch successful: Found existing user (ID: {first_user.id}). Tables exist and contain data.") 
            else:
                app.logger.info("Test fetch successful: No existing users found. Tables exist but are empty.") 
        except Exception as e:
            app.logger.error(f"Error during test fetch from User table: {e}") 
            print(f"CRITICAL ERROR: Test fetch failed from User table: { {e} }", file=sys.stderr)
            app.logger.error("This likely means the database tables were NOT created successfully.") 

        # --- Initialize DBManager and GameManager ---
        global db_manager_instance 
        global game_manager_instance

        db_manager_instance = DBManager(db) 
        app.db_manager = db_manager_instance 
        app.logger.info("DBManager initialized successfully.") 

        game_manager_instance = GameManager(db_manager_instance) 
        app.game_manager = game_manager_instance 
        app.logger.info("GameManager initialized successfully within the application context.") 

        existing_tables = db_manager_instance.get_all_poker_tables()
        if not existing_tables:
            app.logger.info("No poker tables found. Creating a default table...")
            default_table_id = db_manager_instance.create_poker_table(
                name="Default Poker Table",
                small_blind=5,
                big_blind=5,
                max_players=6
            )
            if default_table_id:
                app.logger.info(f"Default poker table created with ID: {default_table_id}")
            else:
                app.logger.error("Failed to create default poker table.")
        else:
            app.logger.info(f"Found {len(existing_tables)} existing poker tables. No default table created.")

    # --- NO user_loader here! It's in auth/routes.py ---
    # --- NO app.after_request log_set_cookie here! ---

    # --- Initialize SocketIO Handlers and Emitters ---
    from .game.sockets.emitters_oop import PokerEmitters
    PokerEmitters.initialize(socketio)

    from .game.sockets import register_socket_handlers
    register_socket_handlers(socketio)

    app.logger.info("App creation complete. Returning app instance.") 
    return app
