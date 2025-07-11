# poker_server/models/table_player.py
from poker_server import db

class TablePlayer(db.Model):
    """
    Model representing a player's participation in a poker table.
    """

    __tablename__ = 'table_players'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Reference to the user playing
    table_id = db.Column(db.Integer, db.ForeignKey('poker_tables.id'), nullable=False)  # Reference to the poker table
    chips_in_table = db.Column(db.Integer, nullable=False)  # Number of chips the player has in the table
    is_active = db.Column(db.Boolean, default=True)  # Whether the player is currently active at the table

    def __repr__(self):
        """
        String representation of the TablePlayer instance for debugging.
        """
        return f"<TablePlayer user={self.user_id} table={self.table_id}>"
