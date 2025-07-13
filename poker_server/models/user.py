# poker_server/models/user.py
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from poker_server import db # ייבוא אובייקט ה-SQLAlchemy
from typing import Dict, Any

class User(UserMixin, db.Model):
    """
    User model for the database.
    Inherits from db.Model for SQLAlchemy and UserMixin for Flask-Login.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False) # Used for login
    nickname = db.Column(db.String(64), unique=True, nullable=False) # ✅ New field for display name
    email = db.Column(db.String(120), unique=True, nullable=True) 
    password_hash = db.Column(db.String(256), nullable=False) 
    balance = db.Column(db.Float, default=10000.0, nullable=False) 
    is_admin = db.Column(db.Boolean, default=False, nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Hashes the password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks if the provided password matches the hashed password."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the User object to a dictionary for JSON serialization.
        Excludes sensitive information like password_hash.
        """
        return {
            "id": self.id,
            "username": self.username,
            "nickname": self.nickname, # ✅ Added to to_dict
            "email": self.email,
            "balance": self.balance, 
            "is_admin": self.is_admin, 
            "created_at": self.created_at.isoformat() if self.created_at else None 
        }

    def __repr__(self):
        return f'<User {self.username} (Nickname: {self.nickname})>' # ✅ Updated repr

