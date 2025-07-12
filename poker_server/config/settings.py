import os

# Get the absolute path of the current directory (i.e., the config folder)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# --- שינוי עבור בסיס נתונים ---
# בייצור (Render), נשתמש במשתנה הסביבה DATABASE_URL שמסופק על ידי Render.
# בפיתוח מקומי, נמשיך להשתמש ב-SQLite.
# חשוב: אם אתה עובר ל-PostgreSQL מקומי בפיתוח, שנה את ברירת המחדל בהתאם.

SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') # ✅ אין יותר ערך ברירת מחדל ל-SQLite

# Disable SQLAlchemy's event system for tracking object modifications
# This saves system resources and is recommended unless events are needed
SQLALCHEMY_TRACK_MODIFICATIONS = False

# --- שינוי עבור SECRET_KEY ---
# בייצור, SECRET_KEY חייב להגיע ממשתנה סביבה.
# לעולם אל תשים מפתח סודי ישירות בקוד בייצור!
# עבור פיתוח מקומי, אתה יכול להגדיר אותו בקובץ .env או להשתמש בערך ברירת מחדל כלשהו,
# אבל ב-Render הוא יגיע ממשתנה הסביבה שתגדיר.
SECRET_KEY = os.getenv('SECRET_KEY', '01d3fe32ba6bfebd9bd08b56d1220cb9a5735d9be683b956')

# SESSION / COOKIE CONFIGURATION
# These settings are important for handling login sessions across different origins

# Allows cookies to be sent with cross-site requests
SESSION_COOKIE_SAMESITE = "None"
# SESSION_COOKIE_SAMESITE = "Lax" # ✅ שינוי זמני לדיבוג מקומי

# Ensures cookies are only sent over HTTPS connections
# Set to False in development (HTTP), True in production (HTTPS)
# בייצור (Render), זה צריך להיות True.
# בפיתוח מקומי (HTTP), זה צריך להיות False.


SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production' # או כל משתנה סביבה אחר שאתה משתמש בו כדי לזהות ייצור
# SESSION_COOKIE_SECURE = False 

# Prevents JavaScript from accessing session cookies (recommended for security)
SESSION_COOKIE_HTTPONLY = True