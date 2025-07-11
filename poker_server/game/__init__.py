  # poker_server/game/__init__.py

from flask import Blueprint

def register_game_blueprints(app):
    from .routes.poker_tables import poker_tables_bp
    from .routes.table_players import table_players_bp
    # בעתיד תוכל להוסיף game_actions_bp

    app.register_blueprint(poker_tables_bp)
    app.register_blueprint(table_players_bp)
