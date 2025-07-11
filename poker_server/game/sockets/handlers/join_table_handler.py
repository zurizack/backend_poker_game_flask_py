# backend/poker_server/game/sockets/handlers/join_table_handler.py

import logging
from typing import Dict, Any, Optional
from flask_socketio import SocketIO, join_room, leave_room
from flask_login import current_user

# ייבוא המופע הגלובלי של game_manager_instance
from backend.poker_server import game_manager_instance 

from backend.poker_server.game.sockets.emitters_oop import PokerEmitters
from backend.poker_server.game.engine.player_oop import Player

logger = logging.getLogger(__name__)

# חתימת הפונקציה כפי שציינת: game_manager אינו פרמטר
def handle_join_table_request(socketio: SocketIO, player_id: int, sid: str, data: Dict[str, Any]) -> Optional[str]:
    """
    מטפל בבקשת שחקן להצטרף לשולחן כצופה.
    :param socketio: מופע ה-SocketIO.
    :param player_id: ה-ID של השחקן (מגיע מ-current_user.id).
    :param sid: ה-Socket ID של השחקן.
    :param data: מילון המכיל 'table_id'.
    :return: ה-ID של השולחן שהשחקן הצטרף אליו בהצלחה, אחרת None.
    """
    table_id_str = data.get('table_id')

    logger.info(f"Handler received join table request: Player ID {player_id}, Table ID: {table_id_str}.")

    # 1. ודא שהנתונים החיוניים קיימים
    if not table_id_str:
        PokerEmitters.emit_error(sid, "Missing table ID for join table request.")
        logger.error(f"Join table request from SID {sid} missing table_id.")
        return None

    table_id = str(table_id_str) # ודא שזה סטרינג

    try:
        # 2. ודא שהמשתמש מאומת ועדכן את אובייקט ה-Player ב-GameManager
        if not current_user.is_authenticated:
            PokerEmitters.emit_error(sid, "Authentication required to join a table.")
            logger.error(f"Unauthenticated user (SID: {sid}) tried to join a table.")
            return None
        
        # ודא שה-player_id שהגיע מהאירוע תואם ל-ID של המשתמש המאומת.
        if player_id != current_user.id:
            logger.warning(f"Player ID mismatch in join table request: event {player_id}, current_user {current_user.id}. Using current_user.id.")
            player_id = current_user.id # ודא עקביות

        # השתמש במופע הגלובלי שיובא
        player_obj: Optional[Player] = game_manager_instance.register_or_update_player_connection(current_user, sid)
        
        if not player_obj:
            PokerEmitters.emit_error(sid, "Failed to retrieve or create player object. Internal error.")
            logger.error(f"Could not get or create player object for authenticated user {current_user.id} (SID: {sid}) in join table handler.")
            return None

        # 3. נסה לצרף את השחקן (כצופה) לשולחן באמצעות GameManager
        # ✅ קריאה למתודה החדשה שתטפל בהוספת צופה ב-GameManager
        success = game_manager_instance.add_player_to_table_as_viewer(player_obj.user_id, table_id) 

        if success:
            join_room(table_id) # צרף את ה-socket לחדר הספציפי של השולחן
            logger.info(f"Player {player_id} (SID: {sid}) successfully joined table {table_id} as a viewer.")
            
            # 4. שלח את מצב השולחן המעודכן ללקוח
            # ✅ קריאה למתודה החדשה שתחזיר את מצב השולחן המלא (כמילון)
            table_state = game_manager_instance.get_table_state(table_id) 
            if table_state:
                # ✅ שימוש ב-PokerEmitters._emit עם שם אירוע מפורש
                PokerEmitters._emit('full_table_state', table_state, sid=sid) 
            else:
                logger.error(f"Table {table_id} not found after player {player_id} joined. This shouldn't happen.")
                PokerEmitters.emit_error(sid, "Internal error: Table state not found.")
                return None # החזר None אם מצב השולחן לא נמצא

            # ✅ שימוש ב-PokerEmitters._emit עם שם אירוע מפורש
            PokerEmitters._emit('join_success', {'message': f"Successfully joined table {table_id}."}, sid=sid)
            return table_id
        else:
            PokerEmitters.emit_error(sid, "Could not join the requested table. It might not exist or another error occurred.")
            logger.warning(f"Handler: Failed to join table {table_id} for player {player_id}.")
            return None

    except Exception as e:
        logger.exception(f"Error handling join table request for player {player_id} (SID: {sid}, Data: {data}): {e}")
        PokerEmitters.emit_error(sid, "An unexpected error occurred while joining the table.")
        return None

