# backend/poker_server/game/engine/game_manager_oop.py

import logging
from typing import Dict, Any, Optional, List

# וודא שהייבואים האלה קיימים:
from backend.poker_server.models.user import User # ודא שזהו מודל ה-User הנכון שלך
from backend.poker_server.game.engine.player_oop import Player # ודא שזהו קובץ ה-Player המעודכן
from backend.poker_server.game.engine.table_oop import Table
from backend.poker_server.sql_services.db_manager import DBManager
from backend.poker_server.game.engine.hand_evaluator_oop import HandEvaluator 


logger = logging.getLogger(__name__)

class GameManager:
    def __init__(self, db_manager: DBManager):
        self._db_manager: DBManager = db_manager 
        self._tables: Dict[str, Table] = {} 
        self._connected_players: Dict[int, Player] = {} # user_id -> Player object
        self.logger = logging.getLogger(__name__)
        self._hand_evaluator = HandEvaluator()
        self.logger.info("HandEvaluator initialized successfully.")
        self._load_existing_tables()
        self.logger.info("GameManager initialized successfully.")
        self.logger.info(f"GameManager: DBManager initialized successfully.") 

    def _load_existing_tables(self):
        poker_tables_data = self._db_manager.get_all_poker_tables() 
        self.logger.info(f"נשלפו {len(poker_tables_data)} שולחנות פוקר מבסיס הנתונים.")

        if poker_tables_data:
            self.logger.info(f"טוען {len(poker_tables_data)} שולחנות קיימים מבסיס הנתונים...")
            for table_data in poker_tables_data:
                table_id = str(table_data['id'])
                table_name = table_data['name'] # שם השולחן
                max_players = table_data['max_players']
                small_blind = table_data['small_blind']
                big_blind = table_data['big_blind']

                poker_table = Table(
                    table_id=table_id,
                    name=table_name, 
                    max_players=max_players,
                    small_blind=small_blind,
                    big_blind=big_blind,
                    hand_evaluator=self._hand_evaluator
                )
                self._tables[table_id] = poker_table
                print(f"שולחן '{table_name}' (ID: {table_id}) נוצר.")
        else:
            self.logger.info("לא נמצאו שולחנות פוקר קיימים בבסיס הנתונים.")

    def get_table_by_id(self, table_id: str) -> Optional[Table]:
        table = self._tables.get(table_id)
        if table:
            self.logger.debug(f"שולחן {table_id} נמצא.")
        else:
            self.logger.warning(f"שולחן {table_id} לא נמצא.")
        return table

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """מחזירה אובייקט Player לפי ה-ID שלו."""
        return self._connected_players.get(player_id)

    def get_player_by_user_id(self, user_id: int) -> Optional[Player]:
        """מחזירה אובייקט Player לפי ה-user_id שלו."""
        return self._connected_players.get(user_id)

    def get_player_id_by_socket_id(self, sid: str) -> Optional[int]:
        """
        מחזירה את ה-user_id של שחקן לפי ה-socket_id שלו.
        """
        for player_id, player_obj in self._connected_players.items():
            if player_obj.socket_id == sid:
                return player_id
        return None

    def update_player_socket_id(self, user_id: int, new_sid: str):
        """מעדכן את ה-socket_id של שחקן קיים."""
        player = self.get_player_by_user_id(user_id)
        if player:
            player.socket_id = new_sid
            self.logger.debug(f"Player {user_id} socket ID updated to {new_sid}.")
        else:
            self.logger.warning(f"Cannot update socket ID for non-existent player {user_id}.")

    def mark_player_reconnected(self, player_id: int):
        """מסמן שחקן כמחובר מחדש (לוגיקה עתידית לטיפול בניתוקים זמניים)."""
        player = self.get_player_by_user_id(player_id)
        if player:
            self.logger.info(f"Player {player_id} marked as reconnected.")
        else:
            self.logger.warning(f"Cannot mark non-existent player {player_id} as reconnected.")

    def mark_player_disconnected(self, player_id: int):
        """מסמן שחקן כמנותק (לוגיקה עתידית לטיפול בניתוקים זמניים וטיימרים)."""
        player = self.get_player_by_user_id(player_id)
        if player:
            self.logger.info(f"Player {player_id} marked as disconnected.")
        else:
            self.logger.warning(f"Cannot mark non-existent player {player_id} as disconnected.")

    # ✅ מתודה חדשה: צירוף שחקן לשולחן כצופה
    def add_player_to_table_as_viewer(self, player_id: int, table_id: str) -> bool:
        """
        מוסיף שחקן לשולחן כצופה.
        :param player_id: ה-ID של השחקן.
        :param table_id: ה-ID של השולחן.
        :return: True אם הצופה נוסף בהצלחה, False אחרת.
        """
        player_obj = self.get_player_by_user_id(player_id)
        if not player_obj:
            self.logger.warning(f"Cannot add viewer: Player {player_id} not found in connected players.")
            return False

        table = self.get_table_by_id(table_id)
        if not table:
            self.logger.warning(f"Cannot add viewer: Table {table_id} not found.")
            return False
        
        # ✅ בדיקה: אם השחקן כבר יושב בשולחן זה, הוא לא יכול להיות צופה בו במקביל
        if player_obj.is_seated_at_table(table_id):
            self.logger.warning(f"Player {player_obj.username} (ID: {player_id}) is already seated at table {table_id}. Cannot add as viewer to the same table.")
            return False

        # קריאה למתודה בתוך אובייקט ה-Table
        success = table.add_viewer(player_obj) 
        if success:
            # ✅ עדכון מצב הצפייה של השחקן באובייקט Player
            player_obj.add_viewing_table(table_id) 
            self.logger.info(f"Player {player_id} added as viewer to table {table_id}.")
            return True
        else:
            self.logger.warning(f"Failed to add player {player_id} as viewer to table {table_id}.")
            return False

    # ✅ מתודה חדשה: צירוף שחקן לשולחן כשחקן יושב (לשעבר join_table)
    def add_player_to_table_as_player(self, player_id: int, table_id: str, buy_in_amount: float, seat_number: int) -> bool:
        """
        מטפל בלוגיקה של שחקן שלוקח מקום בשולחן.
        - מוודא שהשחקן קיים במערכת (מחובר).
        - מוודא שהשולחן והמושב קיימים ותפוסים.
        - מוודא שלשחקן יש מספיק צ'יפים לקנייה.
        - מושיב את השחקן במושב.
        - מעדכן את מצב השולחן.
        """
        self.logger.info(f"Player {player_id} attempting to join table {table_id} at seat {seat_number} with buy-in {buy_in_amount}.")

        player_obj = self.get_player_by_id(player_id)
        if not player_obj:
            self.logger.warning(f"Failed to seat player: Player {player_id} not found in connected players.")
            return False

        table = self.get_table_by_id(table_id)
        if not table:
            self.logger.warning(f"Failed to seat player: Table {table_id} not found.")
            return False

        # ✅ אין צורך לבדוק כאן אם השחקן יושב בשולחן אחר.
        # ההנחה היא ש-player_obj יכול לשבת בכמה שולחנות.
        # הבדיקה אם המושב בשולחן הנוכחי פנוי תתבצע בתוך table.take_seat.
        # הבדיקה אם השחקן כבר יושב *באותו שולחן* תתבצע בתוך table.take_seat.


        # 1. ודא שלשחקן יש מספיק צ'יפים בחשבון הכללי
        # (הערה: player_obj.get_user_total_chips() מחזיר את היתרה הכללית של המשתמש מה-DB)
        if player_obj.get_user_total_chips() < buy_in_amount: 
            self.logger.warning(f"Player {player_id} tried to buy in with {buy_in_amount} but only has {player_obj.get_user_total_chips()} chips in total.")
            return False 

        # 2. נסה להושיב את השחקן בשולחן
        # ✅ ההנחה היא ש-table.take_seat מטפלת ב:
        #    א. בדיקה אם המושב פנוי.
        #    ב. בדיקה אם השחקן כבר יושב במושב זה בשולחן זה (ומניעה).
        #    ג. הסרת השחקן מ-table._viewers אם הוא היה צופה באותו שולחן.
        #    ד. קריאה ל-player_obj.perform_buy_in(self.table_id, buy_in_amount)
        #    ה. קריאה ל-player_obj.set_seated_data_for_table(self.table_id, seat_number)
        #    ו. הוספת השחקן ל-table._players ול-table._seats.
        success = table.take_seat(player_obj, seat_number, buy_in_amount)

        if success:
            # 3. עדכון בסיס הנתונים (צמצום צ'יפים לשחקן) יבוצע ב-SocketIO handler
            #    (ה-handler יבצע session.commit() על אובייקט ה-User ששונה).
            # ❌ שורה זו הוסרה! היא הגורם לבעיה של עדכון כפול ואיפוס צ'יפים.
            # self._db_manager.update_user_chips(player_id, player_obj.get_user_total_chips()) 

            self.logger.info(f"Player {player_id} successfully took seat {seat_number} on table {table_id} with {buy_in_amount} buy-in.")
            return True
        else:
            self.logger.warning(f"Failed to seat player {player_id} at table {table_id}, seat {seat_number}.")
            return False

    # ✅ מתודה חדשה: קבלת מצב שולחן מלא (כמילון)
    def get_table_state(self, table_id: str) -> Optional[Dict[str, Any]]:
        """
        מחזירה את מצב השולחן המלא כמילון, מוכן לשידור ללקוח.
        :param table_id: ה-ID של השולחן.
        :return: מילון המייצג את מצב השולחן, או None אם השולחן לא נמצא.
        """
        table = self.get_table_by_id(table_id)
        if table:
            return table.to_dict() 
        return None

    def register_or_update_player_connection(self, user: User, sid: str) -> Optional[Player]:
        player_id = user.id 
        player = self._connected_players.get(player_id)
        if player:
            if player.socket_id != sid:
                self.logger.info(f"מעדכן את מזהה ה-socket עבור שחקן {player_id} מ-{player.socket_id} ל-{sid}.")
                player.socket_id = sid
            self.logger.info(f"אובייקט Player קיים אוחזר עבור user_id {player_id}.")
        else:
            print(" see the user chips: ", user.chips)
            player = Player(user=user, socket_id=sid) 
            self._connected_players[player_id] = player
            self.logger.info(f"נוצר אובייקט Player חדש עבור user_id <User {user.nickname}> (שם משתמש: {user.nickname}).")
        return player
