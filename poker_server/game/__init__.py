# poker_server/game/__init__.py
import logging # ✅ ייבוא מודול הלוגינג

# הגדרת לוגר ספציפי לקובץ זה
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # וודא שרמת הלוגינג היא INFO

# ייבוא ה-Blueprints
from .routes.poker_tables import poker_tables_bp
from .routes.table_players import table_players_bp

def register_game_blueprints(app):
    logger.info("Inside register_game_blueprints function.") # ✅ שימוש בלוגר המקומי
    
    app.register_blueprint(poker_tables_bp)
    logger.info(f"Blueprint 'poker_tables_bp' registered. URL prefix: {poker_tables_bp.url_prefix}") # ✅ שימוש בלוגר המקומי
    
    app.register_blueprint(table_players_bp)
    logger.info(f"Blueprint 'table_players_bp' registered. URL prefix: {table_players_bp.url_prefix}") # ✅ שימוש בלוגר המקומי
