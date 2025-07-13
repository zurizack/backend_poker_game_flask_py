# poker_server/models/user.py
from datetime import datetime, date # ✅ Import date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .. import db 
from typing import Dict, Any

class User(UserMixin, db.Model):
    """
    User model for the database.
    Inherits from db.Model for SQLAlchemy and UserMixin for Flask-Login.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False) # Used for login
    nickname = db.Column(db.String(64), unique=True, nullable=False) # Display name
    first_name = db.Column(db.String(64), nullable=False) 
    last_name = db.Column(db.String(64), nullable=False)  
    email = db.Column(db.String(120), unique=True, nullable=True) 
    password_hash = db.Column(db.String(256), nullable=False) 
    balance = db.Column(db.Float, default=10000.0, nullable=False) 
    is_admin = db.Column(db.Boolean, default=False, nullable=False) 
    birthdate = db.Column(db.Date, nullable=True) # ✅ New field: birthdate
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
            "nickname": self.nickname, 
            "first_name": self.first_name, 
            "last_name": self.last_name,  
            "email": self.email,
            "balance": self.balance, 
            "is_admin": self.is_admin, 
            "birthdate": str(self.birthdate) if self.birthdate else None, # ✅ Added to to_dict
            "created_at": self.created_at.isoformat() if self.created_at else None 
        }

    def __repr__(self):
        return f"<User {self.username} (Nickname: {self.nickname})>" 

