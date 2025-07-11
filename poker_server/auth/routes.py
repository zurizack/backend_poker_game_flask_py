# poker_server/auth/routes.py
from flask import Blueprint, request, jsonify
from ..models.user import User
from .. import db
from datetime import datetime
from flask_login import login_user, logout_user, current_user
import sys


# Create a Blueprint for authentication routes, prefixing all with /auth
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Route to register a new user
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()  # Parse incoming JSON request body

    # Extract required registration fields from the JSON data
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    nickname = data.get('nickname')
    email = data.get('email')
    password = data.get('password')
    birth_date_str = data.get('birth_date')  # Expected format: 'YYYY-MM-DD'

    # Check that all required fields are present
    if not all([first_name, last_name, nickname, email, password, birth_date_str]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check if the email is already registered
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400

    # Check if the nickname is already taken
    if User.query.filter_by(nickname=nickname).first():
        return jsonify({'error': 'Nickname already exists'}), 400

    # Validate and parse the birth date string to a date object
    try:
        birthdate = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid birth_date format. Use YYYY-MM-DD.'}), 400

    # Create a new User instance with the provided data
    user = User(
        first_name=first_name,
        last_name=last_name,
        nickname=nickname,
        email=email,
        birthdate=birthdate
    )
    user.set_password(password)  # Hash and set the user's password securely

    # Add the new user to the database session and commit
    db.session.add(user)
    db.session.commit()

    # Return a success message upon registration
    return jsonify({'message': 'User registered successfully'}), 201

# Route to log in an existing user
@auth_bp.route('/login', methods=['POST'])
def login():
    print("DEBUG: /auth/login endpoint hit.", file=sys.stderr)
    print(">> Headers:", request.headers, file=sys.stderr)
    print(">> Content-Type:", request.content_type, file=sys.stderr)
    print(">> Raw body:", request.data, file=sys.stderr)
    
    data = request.get_json(silent=True) # השתמש ב-silent=True כדי למנוע שגיאה אם הבקשה אינה JSON
    print(">> JSON body (parsed):", data, file=sys.stderr)
    print(">> Form body:", request.form, file=sys.stderr)

    # Extract login credentials from the request data
    email = data.get('email') if data else None
    nickname = data.get('nickname') if data else None
    password = data.get('password') if data else None

    print(f"DEBUG: Received email: {email}, nickname: {nickname}, password present: {bool(password)}", file=sys.stderr)

    # Ensure password and either email or nickname is provided
    if not password or (not email and not nickname):
        print("DEBUG: Missing login credentials.", file=sys.stderr)
        return jsonify({'error': 'Missing login credentials'}), 400

    user = None
    # Attempt to find user by email if provided
    if email:
        user = User.query.filter_by(email=email).first()
        print(f"DEBUG: User found by email: {user.email if user else 'None'}", file=sys.stderr)
    # Otherwise, try to find by nickname
    elif nickname:
        user = User.query.filter_by(nickname=nickname).first()
        print(f"DEBUG: User found by nickname: {user.nickname if user else 'None'}", file=sys.stderr)

    # Check if user exists and if password matches
    if user is None:
        print("DEBUG: User not found.", file=sys.stderr)
        return jsonify({'error': 'Invalid email/nickname or password'}), 401
    
    if not user.check_password(password):
        print("DEBUG: Password check failed.", file=sys.stderr)
        return jsonify({'error': 'Invalid email/nickname or password'}), 401

    print(f"DEBUG: User {user.nickname} authenticated successfully. Attempting login_user.", file=sys.stderr)
    login_user(user)  # Log in the user via Flask-Login
    print("DEBUG: login_user called successfully.", file=sys.stderr)

    return jsonify({
        'message': 'Logged in successfully',
        'user': {
            'user_id': user.id,
            'username': user.nickname,
            'is_admin': user.is_admin
        }
    })


# Route to log out the current user
@auth_bp.route('/logout', methods=['POST'])
def logout():
    if current_user.is_authenticated:
        logout_user()
        return jsonify({'message': 'Logged out successfully'}), 200
    else:
        return jsonify({'error': 'User not logged in'}), 401
