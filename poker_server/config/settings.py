# poker_server/config/settings.py

import os

# Get the absolute path of the current directory (i.e., the config folder)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Name of the SQLite database file
DB_NAME = 'poker_game.db'

# Construct the full SQLite URI; this places the database one level above the config folder
SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "..", DB_NAME)}'

# Disable SQLAlchemy's event system for tracking object modifications
# This saves system resources and is recommended unless events are needed
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret key used for session signing, CSRF protection, and other security features
# In production, this should be a long, unpredictable, and unique value
SECRET_KEY = 'your_secret_key_here'

# SESSION / COOKIE CONFIGURATION
# These settings are important for handling login sessions across different origins

# Allows cookies to be sent with cross-site requests
SESSION_COOKIE_SAMESITE = "None"

# Ensures cookies are only sent over HTTPS connections
# Set to False in development (HTTP), True in production (HTTPS)
SESSION_COOKIE_SECURE = True

# Prevents JavaScript from accessing session cookies (recommended for security)
SESSION_COOKIE_HTTPONLY = True
