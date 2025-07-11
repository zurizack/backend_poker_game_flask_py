# poker_server/state/public_table_state.py

import json
import logging
from typing import Optional, Dict, Any

# ייבוא לקוח ה-Redis ופונקציות המפתחות המעודכנות
from poker_server.state.client import redis_client
from poker_server.state.keys import get_public_table_state_key
from poker_server.sql_services.table_data import get_table_data_for_server 
from poker_server.state.keys import get_public_table_state_key
from poker_server.game.engine.table_oop import Table


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # הגדר את רמת הלוגים שתרצה (DEBUG, INFO, WARNING, ERROR, CRITICAL)



def get_public_table_state(table_id: str) -> Optional[Dict[str, Any]]:

    """
    שולף את המצב הציבורי של השולחן מ-Redis.
    מפענח Bytes ל-UTF-8 ומבצע deserialization ל-JSON עבור שדות רלוונטיים.
    """
    key = get_public_table_state_key(table_id)
    try:
        data = redis_client.hgetall(key)
        if not data:
            logger.info(f"No public table state found for table ID: {table_id}.")
            return None

        # *** זהו השינוי הקריטי והיחיד שאתה צריך לעשות כאן: ***
        # השורה הזו מטפלת במצב שבו נתוני ה-Redis כבר סטרינגים (בגלל decode_responses=True).
        # אם הנתונים הם עדיין בייטים, היא תפענח אותם.
        if data and next(iter(data.values()), None) and isinstance(next(iter(data.values())), bytes):
            decoded_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in data.items()}
        else:
            decoded_data = data # הנתונים כבר סטרינגים, השתמש בהם ישירות.

        # שדות שצריך לפענח מ-JSON string לאובייקטי Python
        # וודא ש'deck' כלול כאן, כי הוא נשמר כ-JSON string ב-set_public_table_state
        json_fields = [
            'community_cards', 
            'active_player_list',  # <-- השם החדש לשחקנים יושבים
            'spectators_list',     # <-- השם החדש לצופים
            'seats_list',          # <-- השם החדש לכיסאות
            'active_round_bets',   # אם אתה שומר את זה כ-JSON string
            'deck'                 # אם אתה שומר את זה כ-JSON string
        ] 
        for field in json_fields:
            if field in decoded_data and isinstance(decoded_data[field], str) and decoded_data[field]:
                try:
                    decoded_data[field] = json.loads(decoded_data[field])
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON for field '{field}' in table {table_id}: {e}")
                    decoded_data[field] = None

        logger.debug(f"Public table state for {table_id} loaded from Redis.")
        return decoded_data
    except Exception as e:
        logger.error(f"Error getting public table state for {table_id}: {e}", exc_info=True)
        return None

def set_public_table_state(table_id: str, state_data: Dict[str, Any]) -> None:
    """
    שומר את המצב הציבורי של השולחן ל-Redis Hash.
    מבצע serialization ל-JSON עבור אובייקטי Python מורכבים לפני שמירה.
    """
    key = get_public_table_state_key(table_id)
    try:
        data_to_store = {}
        for k, v in state_data.items():
            # המנגנון הזה כבר טוב! הוא יזהה את הרשימות/מילונים החדשים
            # (כמו active_player_list, spectators_list, seats_list)
            # וימיר אותם אוטומטית ל-JSON string.
            if isinstance(v, (dict, list)): # אובייקטים מורכבים הופכים ל-JSON string
                data_to_store[k] = json.dumps(v)
            else: # כל השאר הופכים לסטרינג (מספרים, בוליאנים, סטרינגים רגילים)
                data_to_store[k] = str(v)

        redis_client.hmset(key, data_to_store)
        logger.debug(f"Public table state for {table_id} saved to Redis.")
    except Exception as e:
        logger.error(f"Error setting public table state for {table_id}: {e}", exc_info=True) # הוספתי exc_info=True ללוג מלא


def update_public_table_field(table_id: str, field_name: str, field_value: Any) -> None:
    """
    מעדכן שדה בודד במצב הציבורי של השולחן ב-Redis.
    """
    key = get_public_table_state_key(table_id)
    try:
        if isinstance(field_value, (dict, list)):
            value_to_store = json.dumps(field_value)
        elif isinstance(field_value, bool):
            value_to_store = "true" if field_value else "false"
        else:
            value_to_store = str(field_value)
            
        redis_client.hset(key, field_name, value_to_store)
        logger.debug(f"Updated field '{field_name}' for table {table_id} in Redis.")
    except Exception as e:
        logger.error(f"Error updating field '{field_name}' for table {table_id}: {e}")

def delete_public_table_state(table_id: str) -> None:
    """מוחק את המצב הציבורי של שולחן מ-Redis."""
    key = get_public_table_state_key(table_id)
    try:
        redis_client.delete(key)
        logger.info(f"Public table state for {table_id} deleted from Redis.")
    except Exception as e:
        logger.error(f"Error deleting public table state for {table_id}: {e}")

def initialize_table_in_redis(table_id: str) -> bool:
    """
    מאתחלת שולחן חדש ב-Redis:
    1. שולפת נתונים בסיסיים על השולחן מ-SQL (באמצעות get_table_data_for_server).
    2. יוצרת אובייקט Table בזיכרון.
    3. שומרת את מצב השולחן המלא והציבורי ל-Redis ומאפסת את הצופים,
       **תוך שימוש בפונקציות העזר הקיימות באותה תיקייה.**
    
    מחזירה True אם האתחול הצליח, False אחרת.
    """
    logger.info(f"REDIS INITIALIZER: Attempting to initialize table {table_id} in Redis from SQL data.")
    
    # 1. שליפת נתונים מ-SQL
    sql_data = get_table_data_for_server(table_id) 
    
    if not sql_data:
        logger.warning(f"REDIS INITIALIZER: Table {table_id} not found in SQL database via internal service. Cannot initialize in Redis.")
        return False # נכשל: השולחן לא נמצא ב-SQL

    try:
        # 2. יצירת אובייקט Table בזיכרון
        # ודא ש-ID הוא סטרינג אם ה-Table object מצפה לסטרינג
        new_table_obj = Table(
            table_id=str(sql_data['id']), 
            table_name=sql_data.get('name', 'New Table'),
            small_blind=sql_data.get('small_blind', 5),
            big_blind=sql_data.get('big_blind', 10),
            max_players=sql_data.get('max_players', 6),
            # *** חשוב: הוסף כאן שדות נוספים מ-PokerTable אם הם נדרשים לבנאי של Table! ***
            # לדוגמה:
            # min_buy_in=sql_data.get('min_buy_in', 100), 
            # max_buy_in=sql_data.get('max_buy_in', 1000), 
            # game_type=sql_data.get('game_type', "No Limit Hold'em") 
        )
        logger.debug(f"REDIS INITIALIZER: Table object for {table_id} successfully created from SQL data.")

        # 3. שמירת מצב השולחן המלא והציבורי ב-Redis ואיפוס צופים
        # *** שימוש בפונקציות הקיימות באותה תיקייה (או מיובאות ממנה)! ***

        # א. שמירת המצב הציבורי - משתמשים בפונקציה set_public_table_state שמוגדרת בקובץ זה
        public_state_dict = new_table_obj.to_dict(requesting_player_id=None)
        set_public_table_state(table_id, public_state_dict) 

        # ג. שמירת המצב המלא (private state)
        # מכיוון שאין לך פונקציה ייעודית עבור "full_table_state" כמו get_full_table_state_key,
        # נשמור את זה ישירות ל-Redis באמצעות redis_client
        full_table_key = f"poker:table:{table_id}:full" 
        full_table_data_json = json.dumps(new_table_obj.to_dict(include_deck=True, include_private_player_data=True))
        redis_client.set(full_table_key, full_table_data_json) 

        logger.info(f"REDIS INITIALIZER: Table {table_id} and its associated data successfully initialized in Redis using existing helper functions.")
        return True # הצליח

    except Exception as e:
        logger.error(f"REDIS INITIALIZER: Failed to initialize table {table_id} in Redis: {e}", exc_info=True)
        return False # נכשל: שגיאה במהלך שמירה/יצירה






