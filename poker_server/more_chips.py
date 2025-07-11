# external_chip_updater.py

import sys
import os
import logging

# הגדרת נתיב כדי לאפשר ייבוא מהפרויקט
# יש לוודא שהנתיב הזה מצביע לתיקייה הראשית של הפרויקט שלך
# לדוגמה, אם הסקריפט הזה נמצא ב-poker_server/scripts,
# אז התיקייה הראשית היא התיקייה שמעל backend.
# ייתכן שתצטרך להתאים את הנתיב הזה לסביבת הפרויקט שלך.
script_dir = os.path.dirname(__file__)
# ✅ תיקון: הגדר את project_root כתיקייה הנוכחית של הסקריפט,
# מכיוון שקובץ ה-DB נמצא באותה תיקייה.
project_root = os.path.abspath(script_dir) 
sys.path.insert(0, project_root)

# הגדרות לוגינג בסיסיות לסקריפט
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ✅ ייבוא חדש: Flask ו-Flask-SQLAlchemy
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

try:
    # ייבוא ה-DBManager והמודלים הנדרשים
    from poker_server.sql_services.db_manager import DBManager
    from poker_server.models.user import User as ActualUser # ודא שזהו הייבוא הנכון למודל ה-User שלך
except ImportError as e:
    logger.error(f"שגיאת ייבוא: ודא שנתיבי הייבוא נכונים ושאתה מריץ את הסקריפט מהמיקום הנכון. שגיאה: {e}")
    logger.error(f"נתיב חיפוש Python: {sys.path}")
    sys.exit(1)

# ✅ הגדרת אפליקציית Flask מינימלית ומופע SQLAlchemy
app = Flask(__name__)
# ✅ חשוב: הגדר את נתיב בסיס הנתונים שלך כאן.
# זה חייב להתאים לנתיב שבו קובץ בסיס הנתונים שלך נמצא בפועל.
# לדוגמה, אם קובץ ה-db שלך הוא 'poker_game.db' והוא נמצא בתיקיית הבסיס של הפרויקט,
# אז הנתיב הוא 'sqlite:///' + os.path.join(project_root, 'poker_game.db')
# אם אתה משתמש בבסיס נתונים אחר (PostgreSQL, MySQL), שנה את ה-URI בהתאם.
DATABASE_FILE = 'poker_game.db' # שם קובץ בסיס הנתונים
# ✅ תיקון: DATABASE_PATH כעת מצביע ישירות למיקום הקובץ בתיקיית הסקריפט
DATABASE_PATH = os.path.join(project_root, DATABASE_FILE) 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DATABASE_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app) # אתחול SQLAlchemy עם מופע ה-Flask app

def update_all_players_chips(new_chip_amount: int = 1000):
    """
    מעדכן את מספר הצ'יפים של כל השחקנים בבסיס הנתונים לסכום נתון.
    :param new_chip_amount: כמות הצ'יפים החדשה שכל שחקן יקבל.
    """
    logger.info(f"מתחיל עדכון צ'יפים לכל השחקנים. כמות חדשה: {new_chip_amount}")

    # ✅ בדיקה: ודא שקובץ בסיס הנתונים קיים
    if not os.path.exists(DATABASE_PATH):
        logger.critical(f"שגיאה: קובץ בסיס הנתונים לא נמצא בנתיב: {DATABASE_PATH}. ודא שהנתיב נכון ושהטבלאות נוצרו.")
        logger.critical("ייתכן שיהיה עליך להפעיל את קוד יצירת הטבלאות של האפליקציה הראשית (לרוב db.create_all()).")
        return

    try:
        # ✅ תיקון: העבר את מופע ה-db של SQLAlchemy ל-DBManager
        db_manager = DBManager(db) 
        logger.info("DBManager אותחל בהצלחה ומשתמש באובייקט ה-Flask-SQLAlchemy DB.")
    except Exception as e:
        logger.error(f"שגיאה באתחול DBManager: {e}")
        return

    try:
        # ✅ תיקון: שליפת כל המשתמשים ישירות באמצעות אובייקט ה-db של SQLAlchemy
        # הנחה: ActualUser הוא מודל SQLAlchemy שמופה לטבלת המשתמשים שלך.
        all_users: List[ActualUser] = db.session.query(ActualUser).all()

        if not all_users:
            logger.warning("לא נמצאו משתמשים בבסיס הנתונים לעדכון.")
            return

        logger.info(f"נמצאו {len(all_users)} משתמשים לעדכון.")
        
        updated_count = 0
        for user in all_users:
            try:
                # עדכון הצ'יפים של כל משתמש
                user.chips = new_chip_amount # ✅ עדכון ישיר של שדה הצ'יפים במודל
                db.session.add(user) # ✅ הוסף את האובייקט המעודכן לסשן
                logger.info(f"שחקן {user.nickname} (ID: {user.id}) עודכן ל- {new_chip_amount} צ'יפים.")
                updated_count += 1
            except Exception as e:
                logger.error(f"שגיאה בעדכון צ'יפים לשחקן {user.nickname} (ID: {user.id}): {e}")
                # ניתן להמשיך לשחקן הבא גם אם יש שגיאה באחד
        
        db.session.commit() # ✅ שמור את כל השינויים בבסיס הנתונים
        logger.info(f"סיום עדכון צ'יפים. סך הכל {updated_count} שחקנים עודכנו.")

    except Exception as e:
        db.session.rollback() # ✅ בצע rollback במקרה של שגיאה
        logger.critical(f"שגיאה קריטית במהלך שליפת או עדכון משתמשים: {e}")

if __name__ == "__main__":
    # ✅ הפעלת הפונקציה בתוך קונטקסט של אפליקציית Flask
    with app.app_context():
        update_all_players_chips(1000)
