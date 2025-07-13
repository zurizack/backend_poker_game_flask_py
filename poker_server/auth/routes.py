# poker_server/auth/routes.py
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
import logging
from datetime import datetime 

from ...poker_server import db, login_manager 
from ..models.user import User 

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')
logger = logging.getLogger(__name__) 

@login_manager.user_loader
def load_user(user_id):
    logger.debug(f"Attempting to load user with ID: {user_id}")
    return User.query.get(int(user_id))

@auth_bp.route('/register', methods=['POST'])
def register():
    logger.info("Attempting to register a new user.")
    data = request.get_json()

    if not data:
        logger.warning("Registration failed: No JSON data provided.")
        return jsonify({"message": "No JSON data provided"}), 400

    first_name = data.get('first_name')
    last_name = data.get('last_name')
    username = data.get('username') 
    nickname = data.get('nickname') # ✅ Get nickname from request
    email = data.get('email')
    password = data.get('password')
    birth_date_str = data.get('birth_date') 

    # Basic validation
    if not all([first_name, last_name, username, nickname, email, password, birth_date_str]): # ✅ Added nickname to check
        logger.warning("Registration failed: Missing required fields.")
        return jsonify({"message": "All fields (first_name, last_name, username, nickname, email, password, birth_date) are required"}), 400 # ✅ Updated message
    
    if len(username) < 3 or len(username) > 64:
        logger.warning(f"Registration failed: Username '{username}' length invalid.")
        return jsonify({"message": "Username must be between 3 and 64 characters"}), 400

    if len(nickname) < 3 or len(nickname) > 64: # ✅ Add nickname length validation
        logger.warning(f"Registration failed: Nickname '{nickname}' length invalid.")
        return jsonify({"message": "Nickname must be between 3 and 64 characters"}), 400

    if len(password) < 6:
        logger.warning("Registration failed: Password too short.")
        return jsonify({"message": "Password must be at least 6 characters long"}), 400

    # Validate and parse the birth date string to a date object
    try:
        birthdate = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
    except ValueError:
        logger.warning(f"Registration failed: Invalid birth_date format '{birth_date_str}'.")
        return jsonify({'message': 'Invalid birth_date format. Use YYYY-MM-DD.'}), 400

    # Check if username, nickname or email already exists
    if User.query.filter_by(username=username).first():
        logger.warning(f"Registration failed: Username '{username}' already exists.")
        return jsonify({"message": "Username already exists"}), 409 # Conflict
    
    if User.query.filter_by(nickname=nickname).first(): # ✅ Check if nickname already exists
        logger.warning(f"Registration failed: Nickname '{nickname}' already exists.")
        return jsonify({"message": "Nickname already exists"}), 409 # Conflict
    
    if User.query.filter_by(email=email).first():
        logger.warning(f"Registration failed: Email '{email}' already exists.")
        return jsonify({"message": "Email already exists"}), 409 # Conflict

    new_user = User(
        first_name=first_name,
        last_name=last_name,
        username=username, 
        nickname=nickname, # ✅ Pass nickname to User constructor
        email=email,
        birthdate=birthdate
    )
    new_user.set_password(password) 

    try:
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"User '{username}' (Nickname: '{nickname}') registered successfully.") # ✅ Updated log
        return jsonify({"message": "User registered successfully", "user": new_user.to_dict()}), 201 
    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database integrity error during registration for '{username}' (Nickname: '{nickname}'): {e}", exc_info=True) # ✅ Updated log
        return jsonify({"message": "Database error during registration"}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"An unexpected error occurred during registration for '{username}' (Nickname: '{nickname}'): {e}", exc_info=True) # ✅ Updated log
        return jsonify({"message": "An unexpected error occurred"}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    logger.info("Attempting to log in a user.")
    data = request.get_json()

    if not data:
        logger.warning("Login failed: No JSON data provided.")
        return jsonify({"message": "No JSON data provided"}), 400

    username = data.get('username') 
    password = data.get('password')

    if not username or not password:
        logger.warning("Login failed: Username or password missing.")
        return jsonify({"message": "Username and password are required"}), 400

    user = User.query.filter_by(username=username).first() 

    if user is None or not user.check_password(password):
        logger.warning(f"Login failed: Invalid credentials for username '{username}'.")
        return jsonify({"message": "Invalid username or password"}), 401 

    login_user(user) 
    logger.info(f"User '{username}' (Nickname: '{user.nickname}') logged in successfully.") # ✅ Updated log to show nickname
    return jsonify({"message": "Logged in successfully", "user": user.to_dict()}), 200 

@auth_bp.route('/logout', methods=['POST'])
@login_required 
def logout():
    logger.info(f"Attempting to log out user '{current_user.username}' (Nickname: '{current_user.nickname}').") # ✅ Updated log
    logout_user() 
    logger.info("User logged out successfully.")
    return jsonify({"message": "Logged out successfully"}), 200

@auth_bp.route('/status', methods=['GET'])
def status():
    logger.info("Checking user authentication status.")
    if current_user.is_authenticated:
        logger.info(f"User '{current_user.username}' (Nickname: '{current_user.nickname}') is authenticated.") # ✅ Updated log
        return jsonify({"authenticated": True, "user": current_user.to_dict()}), 200 
    else:
        logger.info("User is not authenticated.")
        return jsonify({"authenticated": False}), 200

