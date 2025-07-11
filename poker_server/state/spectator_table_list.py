# poker_server/state/spectator_table_list.py
import logging
import json
from typing import List, Dict, Any


# ייבוא לקוח ה-Redis ופונקציות המפתחות המעודכנות
from poker_server.state.client import redis_client
from poker_server.state.keys import get_public_table_state_key

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # הגדר את רמת הלוגים שתרצה (DEBUG, INFO, WARNING, ERROR, CRITICAL)



def get_spectators_data_from_redis(table_id: str) -> List[Dict[str, Any]]:
    """
    שולף ומפענח את רשימת הצופים משדה 'spectators_list' ב-Hash של מצב השולחן.
    מחזיר רשימה של מילונים בפייתון.
    """
    key = get_public_table_state_key(table_id)
    try:
        # HGET שולף רק את הערך של שדה ספציפי מתוך ה-Hash
        spectators_json = redis_client.hget(key, 'spectators_list')
        
        if not spectators_json:
            logger.debug(f"No spectators_list found for table {table_id}, returning empty list.")
            return [] # אין צופים או השדה לא קיים
        
        # אם הנתונים ב-Redis הם בייטים, מפענחים ל-UTF-8
        if isinstance(spectators_json, bytes):
            spectators_json = spectators_json.decode('utf-8')
            
        # מפענחים את ה-JSON string לרשימת מילונים של פייתון
        return json.loads(spectators_json)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode spectators_list JSON for table {table_id}: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Error getting spectators_list for table {table_id}: {e}", exc_info=True)
        return []
    

def update_spectators_data_in_redis(table_id: str, spectators_list_data: List[Dict[str, Any]]) -> None:
    """
    מקודד ושומר את רשימת הצופים המעודכנת לשדה 'spectators_list' 
    ב-Hash של מצב השולחן ב-Redis.
    מקבלת רשימה של מילונים של פייתון.
    """
    key = get_public_table_state_key(table_id)
    try:
        # ממירים את רשימת המילונים ל-JSON string לשמירה ב-Redis
        spectators_json = json.dumps(spectators_list_data)
        
        # HSET מעדכן או מוסיף שדה בודד ב-Hash
        redis_client.hset(key, 'spectators_list', spectators_json)
        logger.debug(f"Spectators list for table {table_id} updated in Redis.")
    except Exception as e:
        logger.error(f"Error updating spectators_list for table {table_id}: {e}", exc_info=True)

