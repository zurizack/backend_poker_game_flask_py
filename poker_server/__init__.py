# poker_server/__init__.py
from typing import Optional, Dict, Any, List
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cors import CORS
from flask_socketio import SocketIO
import logging # ייבוא לוגינג

# אתחול אובייקט בסיס הנתונים SQLAlchemy (ללא קונטקסט אפליקציה כאן)
db = SQLAlchemy()

# אתחול מנהל Flask-Login (ללא קונטקסט אפליקציה כאן)
login_manager = LoginManager()

# אתחול SocketIO (ללא קונטקסט אפליקציה כאן)
socketio = SocketIO(cors_allowed_origins="http://localhost:3000", manage_session=False, async_mode='gevent')

# --- ייבוא GameManager ו-DBManager ---
# ודא שהנתיבים האלה נכונים!
from backend.poker_server.sql_services.db_manager import DBManager
from backend.poker_server.game.engine.game_manager_oop import GameManager 

# --- משתנה גלובלי לאחסון מופע GameManager ---
# זה יהיה המופע היחיד של GameManager שיהיה נגיש לכל חלקי האפליקציה.
game_manager_instance: Optional[GameManager] = None
db_manager_instance: Optional[DBManager] = None # הוספנו משתנה גלובלי עבור DBManager גם כן


def create_app():
    """
    פונקציית פקטורי לאפליקציה:
    - יוצרת מופע של אפליקציית פלאסק
    - טוענת קונפיגורציה מ-settings.py
    - מאתחלת הרחבות (SQLAlchemy, LoginManager, SocketIO) עם האפליקציה
    - יוצרת את כל טבלאות בסיס הנתונים בתוך קונטקסט האפליקציה
    - מאתחלת GameManager ו-DBManager
    - רושמת את ה-blueprints של האימות והמשחק
    - מחזירה את מופע האפליקציה המוגדר
    """
    app = Flask(__name__)

    app.config.from_pyfile('config/settings.py')  # טוען קונפיגורציה מקובץ חיצוני

    # הפעלת CORS עם תמיכה ב-credentials עבור מקור הפרונטאנד
    CORS(app, supports_credentials=True, origins=["http://localhost:3000"])

    # קשירת מופעי SQLAlchemy ו-LoginManager לאפליקציה זו
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app)

    # --- יצירת טבלאות בסיס נתונים ---
    with app.app_context():
        # ייבוא המודלים שלך כדי ש-db.create_all() יזהה אותם
        from .models.user import User
        from .models.poker_table import PokerTable
        #from .models.table_player import TablePlayer # אם קיים אצלך - ודא שזה נכון

        db.create_all() # יוצר את כל הטבלאות עבור המודלים שהוגדרו
        logging.info("טבלאות בסיס הנתונים נוצרו/עודכנו בהצלחה.")

        # --- אתחול DBManager ו-GameManager ---
        # נשתמש במשתנים הגלובליים
        global db_manager_instance 
        global game_manager_instance

        # ✅ שלב 1: יצירת מופע של DBManager והעברת אובייקט ה-db של Flask-SQLAlchemy
        db_manager_instance = DBManager(db) 
        # ניתן לשמור אותו על אובייקט האפליקציה לנוחות גישה עתידית
        app.db_manager = db_manager_instance 
        logging.info("DBManager אותחל בהצלחה.") # לוג עבור DBManager

        # ✅ שלב 2: יצירת מופע של GameManager והעברת מופע ה-DBManager שיצרנו
        game_manager_instance = GameManager(db_manager_instance) 
        # ניתן לשמור אותו על אובייקט האפליקציה לנוחות גישה עתידית
        app.game_manager = game_manager_instance 
        logging.info("GameManager אותחל בהצלחה בתוך קונטקסט האפליקציה.") # לוג עבור GameManager


    # --- הגדרת טוען המשתמש של Flask-Login ---
    @login_manager.user_loader
    def load_user(user_id):
        """
        Flask-Login user loader callback.
        בהינתן ID משתמש (כסטרינג), מחזיר את אובייקט ה-User או None.
        זה משמש לטעינה מחדש של המשתמש מהסשן.
        """
        # עכשיו אנחנו יכולים להשתמש ב-DBManager כדי לטעון את המשתמש
        # מכיוון ש-db_manager_instance הוא גלובלי, נוכל לגשת אליו ישירות.
        # הערה: Flask-Login מצפה לאובייקט User, לא למילון.
        # לכן, נצטרך לשלוף את אובייקט ה-User המלא מה-DB.
        # נשתמש ב-db_manager_instance.get_user_by_id() (אם הוא מחזיר אובייקט User מלא)
        # או ב-User.query.get() ישירות אם זהו הקונטקסט של Flask-Login.
        # עדיף להשתמש ב-DBManager לגישה עקבית.
        if db_manager_instance: # ודא ש-db_manager_instance כבר אותחל
            return db_manager_instance.get_user_by_id(int(user_id))
        else:
            # אם מסיבה כלשהי db_manager_instance עדיין לא אותחל (מקרה קצה),
            # נחזור לגישה ישירה למודל.
            from .models.user import User # ייבוא מקומי כדי למנוע Circular Import
            return User.query.get(int(user_id))

    @app.after_request
    def log_set_cookie(response):
        # למטרות דיבוג של קוקיז, ניתן להחליף בלוגינג מתאים
        return response

    # --- רישום Blueprints ---
    from .auth.routes import auth_bp
    from .game import register_game_blueprints 

    app.register_blueprint(auth_bp)
    register_game_blueprints(app) # קריאה לפונקציה שרושמת Blueprints של משחק

    # --- אתחול SocketIO Handlers ו-Emitters ---
    from backend.poker_server.game.sockets.emitters_oop import PokerEmitters
    PokerEmitters.initialize(socketio) # ודא ש-PokerEmitters מקבל את socketio

    from backend.poker_server.game.sockets import register_socket_handlers
    register_socket_handlers(socketio) # ודא ש-register_socket_handlers מקבל את socketio

    return app