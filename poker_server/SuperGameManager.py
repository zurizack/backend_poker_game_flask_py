# poker_server/SuperGameManager.py

from typing import Dict, Optional, Any
# ייבוא המחלקות העיקריות שאותן ה-SuperGameManager ינהל או ישתמש בהן
from backend.poker_server.game.engine.table_oop import Table 
from backend.poker_server.game.engine.game_manager_oop import Game_Manager
from backend.poker_server.game.engine.player_oop import Player

# נניח שאתה משתמש במודול נפרד לגישה ל-Redis (או כל Persistent Storage אחר)
# זה רק דוגמה לאיך תיראה הקריאה.
# בפועל, תצטרך לממש את הפונקציות האלה במודול redis_data_accessor.
# from poker_server.data_access import redis_data_accessor 


class SuperGameManager:
    """
    מנהל העל של השרת.
    אחראי על ניהול כל אובייקטי Game_Manager (ולכן גם Table) הפעילים בזיכרון.
    הוא מוודא שכל שולחן מיוצג על ידי מופע יחיד של Game_Manager בזיכרון.
    """
    
    # שימוש ב-Singleton Pattern כדי לוודא שיש רק מופע אחד של SuperGameManager בכל השרת.
    _instance: Optional['SuperGameManager'] = None 

    def __new__(cls):
        """
        מוודא יצירת מופע יחיד של SuperGameManager.
        אם כבר קיים מופע, מחזיר אותו. אחרת, יוצר חדש.
        """
        if cls._instance is None:
            cls._instance = super(SuperGameManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        אתחול פנימי של ה-SuperGameManager. נקרא רק פעם אחת.
        """
        # מילון לאחסון כל אובייקטי ה-Game_Manager הפעילים.
        # המפתח יהיה table_id (str) והערך יהיה אובייקט Game_Manager.
        self.active_game_managers: Dict[str, Game_Manager] = {}
        print("SuperGameManager initialized and ready.")

    def get_game_manager(self, table_id: str) -> Optional[Game_Manager]:
        """
        מחזירה את אובייקט ה-Game_Manager החי והפעיל עבור ID שולחן נתון.
        """
        return self.active_game_managers.get(table_id)

    def load_or_create_table_and_manager(self, 
                                        table_id: str, 
                                        table_name: str = "Default Table", # ערך ברירת מחדל
                                        max_players: int = 6,              # ערך ברירת מחדל
                                        small_blind: int = 10,             # ערך ברירת מחדל
                                        big_blind: int = 20                # ערך ברירת מחדל
                                        ) -> Optional[Game_Manager]:
        """
        טוען מצב שולחן קיים מזיכרון ה-RAM או ממסד נתונים (Redis),
        או יוצר שולחן חדש לחלוטין אם לא נמצא קיים.
        מפעיל את השולחן ואת מנהל המשחק שלו בזיכרון השרת.

        Args:
            table_id (str): המזהה הייחודי של השולחן.
            table_name (str): שם השולחן (משמש ליצירה חדשה).
            max_players (int): מספר השחקנים המקסימלי (משמש ליצירה חדשה).
            small_blind (int): הבליינד הקטן (משמש ליצירה חדשה).
            big_blind (int): הבליינד הגדול (משמש ליצירה חדשה).

        Returns:
            Optional[Game_Manager]: אובייקט Game_Manager המייצג את השולחן הפעיל, או None אם הייתה שגיאה.
        """
        # 1. בדוק אם השולחן כבר פעיל בזיכרון ה-RAM
        if table_id in self.active_game_managers:
            print(f"SuperGameManager: Table {table_id} is already active in memory. Returning existing manager.")
            return self.active_game_managers[table_id]

        print(f"SuperGameManager: Attempting to load or create table {table_id}...")
        try:
            table_obj = None
            # 2. נסה לטעון את מצב השולחן ממסד נתונים קבוע (לדוגמה, Redis)
            # אם היית משתמש ב-redis_data_accessor, הקריאה הייתה נראית כך:
            # table_data_from_db = redis_data_accessor.get_table_data(table_id)
            
            # לצורך הדוגמה כאן, נדמה שאין נתונים ב-DB בפעם הראשונה:
            table_data_from_db = None 

            if table_data_from_db:
                # אם נמצאו נתונים ב-DB, צור אובייקט Table מהם
                table_obj = Table.from_dict(table_data_from_db)
                print(f"SuperGameManager: Table {table_id} loaded from persistent storage.")
            else:
                # אם לא נמצאו נתונים ב-DB, צור שולחן חדש לגמרי
                table_obj = Table(table_id, table_name, max_players, small_blind, big_blind)
                print(f"SuperGameManager: New Table {table_id} created in memory.")
                # בנקודה זו, ניתן לשמור את מצב הבסיס של השולחן החדש ל-DB
                # redis_data_accessor.save_table_data(table_id, table_obj.to_dict())

            # 3. צור אובייקט Game_Manager חדש שייקח אחריות על ניהול ה-Table הזה
            game_manager_obj = Game_Manager(table=table_obj)
            
            # 4. שמור את ה-Game_Manager החדש במילון השולחנות הפעילים
            # כעת הוא "חי" בזיכרון השרת וניתן לגשת אליו.
            self.active_game_managers[table_id] = game_manager_obj
            print(f"SuperGameManager: Table {table_id} successfully activated in memory.")
            return game_manager_obj
        except Exception as e:
            print(f"SuperGameManager: Error loading/creating table {table_id}: {e}")
            # במקרה של שגיאה, נדפיס ונחזיר None
            return None

    def deactivate_table_and_manager(self, table_id: str) -> bool:
        """
        מבטל את הפעלת שולחן ספציפי מהזיכרון של השרת.
        שומר את מצבו הסופי של השולחן למסד נתונים קבוע (Redis) לפני מחיקתו מהזיכרון.

        Args:
            table_id (str): המזהה הייחודי של השולחן לביטול הפעלה.

        Returns:
            bool: True אם השולחן בוטל בהצלחה, False אחרת.
        """
        if table_id in self.active_game_managers:
            game_manager = self.active_game_managers[table_id]
            
            # 1. שמור את המצב הנוכחי והסופי של השולחן למסד הנתונים הקבוע
            # זה קריטי כדי לשמר את השינויים (כמו סטאקים של שחקנים, קופות וכו')
            table_state_to_save = game_manager.table.to_dict(include_private_player_data=False) 
            print(f"SuperGameManager: Saving final state of table {table_id} to persistent storage (mock/Redis).")
            # אם היית משתמש ב-redis_data_accessor, הקריאה הייתה נראית כך:
            # redis_data_accessor.save_table_data(table_id, table_state_to_save)

            # 2. הסר את אובייקט ה-Game_Manager מהזיכרון הפעיל
            del self.active_game_managers[table_id]
            print(f"SuperGameManager: Table {table_id} deactivated and removed from memory.")
            return True
        print(f"SuperGameManager: Table {table_id} not found as active. No deactivation needed.")
        return False

# יצירת מופע גלובלי יחיד של SuperGameManager.
# חשוב: שורה זו צריכה להתבצע פעם אחת בלבד, בטעינה הראשונית של השרת.
# כל חלק אחר בשרת ייבא את המופע הזה ישירות.
super_game_manager_instance = SuperGameManager()