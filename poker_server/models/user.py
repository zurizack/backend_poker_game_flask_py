# poker_server/models/user.py
from .. import db  # Import the SQLAlchemy database instance from the parent package
from flask_login import UserMixin  # Mixin providing default implementations for Flask-Login user methods
from werkzeug.security import generate_password_hash, check_password_hash  # For secure password hashing and verification
from datetime import date

class User(UserMixin, db.Model):
    """
    User model representing registered users in the system.
    Implements Flask-Login's UserMixin for session management.
    """

    __tablename__ = 'users'  # Specify the table name in the database

    # Define the columns of the users table
    id = db.Column(db.Integer, primary_key=True)  # Primary key unique user ID
    first_name = db.Column(db.String(50), nullable=False)  # User's first name, required
    last_name = db.Column(db.String(50), nullable=False)   # User's last name, required
    email = db.Column(db.String(120), unique=True, nullable=False)  # User's email, unique and required
    nickname = db.Column(db.String(50), unique=True, nullable=False)  # Unique user nickname, required
    password_hash = db.Column(db.String(256), nullable=False)  # Hashed password, required
    birthdate = db.Column(db.Date, nullable=True)  # Optional birthdate field
    chips = db.Column(db.Float, default=10000.0)  # Default chips assigned to user (e.g., poker chips)
    is_admin = db.Column(db.Boolean, default=False)  # Flag to mark admin users, default is False

    def set_password(self, password):
        """
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verify if the given plain-text password matches the stored hashed password.
        """
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """
        Representation for debugging: show user by nickname.
        """
        return f"<User {self.nickname}>"

    def to_dict(self):
        """
        Converts the User object to a dictionary suitable for JSON serialization.
        """
        return {
            'id': self.id,
            'nickname': self.nickname,
            'chips': self.chips,
            # 'first_name': self.first_name, # You can add more fields if needed on the client side
            # 'last_name': self.last_name,
            # 'email': self.email,
            # 'is_admin': self.is_admin,
            # Note: Do not expose password_hash!
            # For birthdate, you might want to convert it to a string if you add it:
            # 'birthdate': self.birthdate.isoformat() if self.birthdate else None
        }
