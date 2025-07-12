  # poker_server/game/__init__.py
import logging
logging.info("Inside register_game_blueprints function.")
from .routes.poker_tables import poker_tables_bp
from .routes.table_players import table_players_bp


def register_game_blueprints(app):

    app.register_blueprint(poker_tables_bp)
    logging.info(f"Blueprint 'poker_tables_bp' registered. URL prefix: {poker_tables_bp.url_prefix}") 

    app.register_blueprint(table_players_bp)
    logging.info(f"Blueprint 'table_players_bp' registered. URL prefix: {table_players_bp.url_prefix}") 

