# poker_server/models/poker_table.py

from backend.poker_server import db

class PokerTable(db.Model):
    """
    Model representing a poker table in the database.
    """

    __tablename__ = 'poker_tables'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # Name of the poker table
    small_blind = db.Column(db.Integer, nullable=False)  # Small blind amount for the table
    big_blind = db.Column(db.Integer, nullable=False)  # Big blind amount for the table
    max_players = db.Column(db.Integer, default=9)  # Maximum number of players allowed at the table
    created_at = db.Column(db.DateTime, server_default=db.func.now())  # Timestamp of table creation

    def __repr__(self):
        """
        String representation of the PokerTable instance for debugging.
        """
        return f"<PokerTable {self.name}>"
