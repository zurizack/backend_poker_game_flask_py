# poker_server/sql_services/table_data.py

from flask import jsonify
from poker_server.models.poker_table import PokerTable
from typing import Optional, Dict, Any
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_table_data_from_sql_db(table_id):
    
    table = PokerTable.query.get(table_id)
    if not table:
        return jsonify({'error': 'Table not found'}), 404

    return jsonify({
        'id': table.id,
        'name': table.name,
        'max_players': table.max_players,
        'small_blind': table.small_blind,
        'big_blind': table.big_blind
    })

def get_table_data_for_server(table_id: str) -> Optional[Dict[str, Any]]:
    """
    **פונקציית שירות פנימית בלבד!**
    שולפת נתונים בסיסיים על שולחן ספציפי מבסיס הנתונים ה-SQL.
    מחזירה מילון פייתון טהור עם נתוני השולחן, או None אם השולחן לא נמצא.
    אינה מטפלת בתגובות HTTP (jsonify).
    """
    logger.info(f"SQL Service (Internal): Fetching basic table data for table ID: {table_id} from SQL DB.")
    
    try:
        table = PokerTable.query.get(table_id)
        
        if not table:
            logger.warning(f"SQL Service (Internal): Table {table_id} not found in SQL database.")
            return None # מחזירים None כששולחן לא נמצא
        
        # בונים מילון עם הנתונים המינימליים הנדרשים לאתחול אובייקט ה-Table ב-Redis
        # ודא שכל השדות האלה קיימים במודל PokerTable שלך ומועברים לבנאי של Table.
        return {
            'id': str(table.id), # ודא ש-ID הוא סטרינג אם ה-Table object מצפה לסטרינג
            'name': table.name,
            'max_players': table.max_players,
            'small_blind': table.small_blind,
            'big_blind': table.big_blind,
            # *** חשוב: הוסף כאן שדות נוספים מ-PokerTable אם הם נדרשים לבנאי של Table! ***
            # לדוגמה, אם יש לך עמודות ב-PokerTable עבור buy-in וסוג משחק:
            # 'min_buy_in': table.min_buy_in,
            # 'max_buy_in': table.max_buy_in,
            # 'game_type': table.game_type,
        }
    except Exception as e:
        logger.error(f"SQL Service (Internal): Error fetching table {table_id} from SQL DB: {e}", exc_info=True)
        return None
