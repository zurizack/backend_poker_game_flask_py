# poker_server/auth/routes.py
from flask import Blueprint, request, jsonify
from backend.poker_server.models.user import User
from backend.poker_server import db
from datetime import datetime
from flask_login import login_user, logout_user, current_user


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
    print(">> Headers:", request.headers)
    print(">> Content-Type:", request.content_type)
    print(">> Raw body:", request.data)
    print(">> JSON body:", request.get_json(silent=True))
    print(">> Form body:", request.form)
    data = request.get_json()  # Parse incoming JSON request body

    # Extract login credentials from the request data
    email = data.get('email')
    nickname = data.get('nickname')
    password = data.get('password')

    # Ensure password and either email or nickname is provided
    if not password or (not email and not nickname):
        return jsonify({'error': 'Missing login credentials'}), 400

    user = None
    # Attempt to find user by email if provided
    if email:
        user = User.query.filter_by(email=email).first()
    # Otherwise, try to find by nickname
    elif nickname:
        user = User.query.filter_by(nickname=nickname).first()

    # Check if user exists and if password matches
    if user is None or not user.check_password(password):
        return jsonify({'error': 'Invalid email/nickname or password'}), 401

    login_user(user)  # Log in the user via Flask-Login
    return jsonify({
        'message': 'Logged in successfully',
        'user': {
            'user_id': user.id,
            'username': user.nickname,
            'is_admin': user.is_admin  # אם יש שדה כזה
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
