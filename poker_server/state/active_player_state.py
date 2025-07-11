# poker_server/state/active_player_state.py

import json
import logging
from typing import List, Dict, Any

# ייבוא לקוח ה-Redis ופונקציות המפתחות המעודכנות
from poker_server.state.client import redis_client
from poker_server.state.keys import get_public_table_state_key


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # הגדר את רמת הלוגים שתרצה (DEBUG, INFO, WARNING, ERROR, CRITICAL)


def get_active_players_data_from_redis(table_id: str) -> List[Dict[str, Any]]:
    """
    שולף ומפענח את רשימת השחקנים הפעילים משדה 'active_player_list' ב-Hash של מצב השולחן.
    מחזיר רשימה של מילונים בפייתון.
    """
    key = get_public_table_state_key(table_id)
    try:
        # HGET שולף רק את הערך של שדה ספציפי מתוך ה-Hash
        players_json = redis_client.hget(key, 'active_player_list')
        
        if not players_json:
            logger.debug(f"No active_player_list found for table {table_id}, returning empty list.")
            return [] # אין שחקנים פעילים או השדה לא קיים
        
        # אם הנתונים ב-Redis הם בייטים, מפענחים ל-UTF-8
        if isinstance(players_json, bytes):
            players_json = players_json.decode('utf-8')
            
        # מפענחים את ה-JSON string לרשימת מילונים של פייתון
        return json.loads(players_json)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode active_player_list JSON for table {table_id}: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Error getting active_player_list for table {table_id}: {e}", exc_info=True)
        return []
    

def update_active_players_data_in_redis(table_id: str, players_list_data: List[Dict[str, Any]]) -> None:
    """
    מקודד ושומר את רשימת השחקנים הפעילים המעודכנת לשדה 'active_player_list' 
    ב-Hash של מצב השולחן ב-Redis.
    מקבלת רשימה של מילונים של פייתון.
    """
    key = get_public_table_state_key(table_id)
    try:
        # ממירים את רשימת המילונים ל-JSON string לשמירה ב-Redis
        players_json = json.dumps(players_list_data)
        
        # HSET מעדכן או מוסיף שדה בודד ב-Hash
        redis_client.hset(key, 'active_player_list', players_json)
        logger.debug(f"Active players list for table {table_id} updated in Redis.")
    except Exception as e:
        logger.error(f"Error updating active_player_list for table {table_id}: {e}", exc_info=True)



