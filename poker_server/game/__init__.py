  # poker_server/game/__init__.py
def register_game_blueprints(app):
    from .routes.poker_tables import poker_tables_bp
    from .routes.table_players import table_players_bp

    app.register_blueprint(poker_tables_bp)
    app.register_blueprint(table_players_bp)
