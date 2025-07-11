# backend/poker_server/data/db_manager.py

import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session # לטיפוס סשן עבור רמזים
from datetime import date

# --- ודא שנתיבי הייבוא האלה נכונים בהתאם למבנה הפרויקט שלך ---
# אובייקט ה-db של Flask-SQLAlchemy (מתוך __init__.py של poker_server)
from .. import db 
# מודלים של בסיס הנתונים
from ..models.user import User
from ..models.poker_table import PokerTable

# הגדרת לוגר עבור DBManager
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DBManager:
    """
    מנהל את האינטראקציה עם בסיס הנתונים באמצעות SQLAlchemy (מבוסס על Flask-SQLAlchemy).
    אחראי על שמירת וטעינת נתוני שחקנים ושולחנות.
    מממש Singleton Pattern כדי להבטיח מופע יחיד של המנהל.
    """
    _instance: Optional['DBManager'] = None # רמז טיפוס למופע הסינגלטון

    def __new__(cls, flask_db_instance: Any):
        """
        מממש את דפוס הסינגלטון עבור DBManager.
        :param flask_db_instance: אובייקט ה-db של Flask-SQLAlchemy המאותחל.
        """
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            cls._instance._db = flask_db_instance
            logger.info("DBManager אותחל בהצלחה ומשתמש באובייקט ה-Flask-SQLAlchemy DB.")
        return cls._instance

    def get_session(self) -> Session:
        """
        מחזירה את סשן בסיס הנתונים הנוכחי של Flask-SQLAlchemy.
        """
        return self._db.session

    # --- ניהול משתמשים (User) ---

    def register_user(self, first_name: str, last_name: str, email: str, nickname: str, password: str, birthdate: Optional[date] = None, initial_chips: int = 1000) -> Optional[int]:
        """
        רושם משתמש חדש בבסיס הנתונים.
        מחזיר את ה-ID של המשתמש שנרשם, או None אם הכינוי/אימייל כבר תפוסים.
        """
        session = self.get_session()
        try:
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                nickname=nickname,
                chips=initial_chips,
                birthdate=birthdate # יכול להיות None
            )
            new_user.set_password(password) # משתמש במתודה הקיימת במודל User
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user) # רענן את האובייקט כדי לקבל את ה-ID החדש
            logger.info(f"משתמש '{nickname}' (ID: {new_user.id}) נרשם בהצלחה.")
            return new_user.id
        except IntegrityError:
            session.rollback() # מבטל שינויים אם יש הפרת ייחודיות (כינוי/אימייל כבר קיימים)
            logger.warning(f"שגיאה: שם המשתמש או האימייל של '{nickname}' כבר קיימים.")
            return None
        except Exception as e:
            session.rollback()
            logger.error(f"שגיאה ברישום משתמש '{nickname}': {e}", exc_info=True)
            return None
        finally:
            session.close() # סוגר את הסשן

    def authenticate_user(self, nickname: str, password: str) -> Optional[Dict]:
        """
        מאמת משתמש ומחזיר את נתוניו הבסיסיים אם האימות הצליח.
        :return: מילון עם נתוני המשתמש (id, nickname, chips, is_admin) או None אם האימות נכשל.
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.nickname == nickname).first()

            if user:
                if user.check_password(password): # משתמש במתודה הקיימת במודל User
                    logger.info(f"משתמש '{nickname}' אומת בהצלחה.")
                    return {
                        "id": user.id,
                        "nickname": user.nickname,
                        "chips": user.chips,
                        "is_admin": user.is_admin,
                        "first_name": user.first_name, # הוספתי שדות נוספים שקיימים במודל
                        "last_name": user.last_name,
                        "email": user.email
                    }
                else:
                    logger.warning(f"שגיאה: סיסמה שגויה עבור '{nickname}'.")
                    return None
            else:
                logger.warning(f"שגיאה: שם המשתמש '{nickname}' לא נמצא.")
                return None
        except Exception as e:
            logger.error(f"שגיאה באימות משתמש '{nickname}': {e}", exc_info=True)
            return None
        finally:
            session.close()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        שולפת אובייקט User ממסד הנתונים לפי ה-ID שלו.
        הערה: המתודה הזו מחזירה אובייקט User ישירות, לא מילון.
        """
        session = self.get_session()
        try:
            # שימוש ב-get() עבור Primary Key הוא יעיל יותר
            user = session.get(User, user_id) 
            if user:
                logger.debug(f"User {user_id} fetched successfully from DB: {user.nickname}.")
            else:
                logger.warning(f"User {user_id} not found in DB.")
            return user
        except Exception as e:
            logger.error(f"Error fetching user {user_id} from DB: {e}", exc_info=True)
            return None
        finally:
            session.close()

    def get_user_data(self, user_id: int) -> Optional[Dict]:
        """
        מחזירה את כל נתוני המשתמש מה-DB לפי ID.
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                return {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "nickname": user.nickname,
                    "chips": user.chips,
                    "is_admin": user.is_admin,
                    "birthdate": str(user.birthdate) if user.birthdate else None # המרה לסטרינג אם קיים
                }
            logger.warning(f"לא נמצא משתמש עם ID: {user_id}.")
            return None
        except Exception as e:
            logger.error(f"שגיאה בקבלת נתוני משתמש {user_id}: {e}", exc_info=True)
            return None
        finally:
            session.close()

    def save_user_changes(self, user: User):
        """
        שומרת שינויים שבוצעו באובייקט User (כמו עדכון צ'יפים).
        """
        session = self.get_session()
        try:
            # האובייקט user אמור להיות כבר "attached" לסשן אם הוא נשלף ממנו.
            # אם הוא לא, session.add(user) תוסיף אותו.
            session.add(user) 
            session.commit()
            logger.debug(f"User {user.id} changes saved to DB. New chips: {user.chips}.")
        except Exception as e:
            session.rollback() 
            logger.error(f"Error saving user {user.id} changes to DB: {e}", exc_info=True)
        finally:
            session.close()

    def update_user_chips(self, user_id: int, new_chips_amount: int) -> bool:
        """
        מעדכן את כמות הצ'יפים של משתמש בבסיס הנתונים.
        """
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.chips = new_chips_amount
                session.commit()
                logger.info(f"צ'יפים של משתמש {user_id} עודכנו ל: {new_chips_amount}.")
                return True
            logger.warning(f"אזהרה: לא נמצא משתמש עם ID {user_id} לעדכון צ'יפים.")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"שגיאה בעדכון צ'יפים למשתמש {user_id}: {e}", exc_info=True)
            return False
        finally:
            session.close()

    # --- ניהול שולחנות פוקר (PokerTable) ---

    def get_table_data_for_server(self, table_id: int) -> Optional[Dict[str, Any]]:
        """
        שולפת נתונים בסיסיים על שולחן פוקר ספציפי מבסיס הנתונים.
        מחזירה מילון פייתון טהור עם נתוני השולחן, או None אם השולחן לא נמצא.
        (הועברה מ-poker_server/sql_services/table_data.py)
        """
        logger.info(f"DBManager: Fetching basic table data for table ID: {table_id}.")
        session = self.get_session()
        try:
            # שימוש ב-get() עבור Primary Key הוא יעיל
            table = session.query(PokerTable).get(table_id) 
            
            if not table:
                logger.warning(f"DBManager: Table {table_id} not found in SQL database.")
                return None
            
            return {
                'id': table.id, # נשאר int כפי שמוגדר במודל
                'name': table.name,
                'max_players': table.max_players,
                'small_blind': table.small_blind,
                'big_blind': table.big_blind,
                'created_at': str(table.created_at) # המרה לסטרינג לייצוג נוח
            }
        except Exception as e:
            session.rollback() # ודא שחרור אם יש שגיאה
            logger.error(f"DBManager: Error fetching table {table_id} from SQL DB: {e}", exc_info=True)
            return None
        finally:
            session.close()

    def create_poker_table(self, name: str, small_blind: int, big_blind: int, max_players: int = 9) -> Optional[int]:
        """
        יוצר שולחן פוקר חדש בבסיס הנתונים.
        מחזיר את ה-ID של השולחן שנוצר, או None אם הייתה שגיאה.
        """
        session = self.get_session()
        try:
            new_table = PokerTable(
                name=name,
                small_blind=small_blind,
                big_blind=big_blind,
                max_players=max_players
            )
            session.add(new_table)
            session.commit()
            session.refresh(new_table) # כדי לקבל את ה-ID החדש
            logger.info(f"שולחן פוקר '{name}' (ID: {new_table.id}) נוצר בהצלחה.")
            return new_table.id
        except Exception as e:
            session.rollback()
            logger.error(f"שגיאה ביצירת שולחן פוקר '{name}': {e}", exc_info=True)
            return None
        finally:
            session.close()

    def get_all_poker_tables(self) -> List[Dict[str, Any]]:
        """
        מחזירה רשימה של כל שולחנות הפוקר הקיימים בבסיס הנתונים.
        """
        session = self.get_session()
        tables_data = []
        try:
            tables = session.query(PokerTable).all()
            for table in tables:
                tables_data.append({
                    'id': table.id,
                    'name': table.name,
                    'max_players': table.max_players,
                    'small_blind': table.small_blind,
                    'big_blind': table.big_blind,
                    'created_at': str(table.created_at)
                })
            logger.info(f"נשלפו {len(tables_data)} שולחנות פוקר מבסיס הנתונים.")
            return tables_data
        except Exception as e:
            logger.error(f"שגיאה בשליפת כל שולחנות הפוקר: {e}", exc_info=True)
            return []
        finally:
            session.close()

    # ... (ניתן להוסיף כאן מתודות נוספות לפי הצורך, למשל: update_table_settings, delete_table) ...