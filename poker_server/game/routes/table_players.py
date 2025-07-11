# poker_server/game/routes/table_players.py

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.poker_server import db
from backend.poker_server.models.table_player import TablePlayer
from backend.poker_server.models.poker_table import PokerTable
# from poker_server.state.broadcast import broadcast_players_update


table_players_bp = Blueprint('table_players', __name__, url_prefix='/game')


@table_players_bp.route('/join_table/<int:table_id>', methods=['POST'])
@login_required
def join_table(table_id):
    """
    Allows a logged-in user to join a specific poker table.

    Validates that:
    - The table exists
    - The user is not already seated at the table
    - The table has an available seat

    Once validated, creates a new TablePlayer record,
    commits it to the database, broadcasts an update to other players,
    and returns the updated list of players.
    """
    table = PokerTable.query.get(table_id)
    if not table:
        return jsonify({'error': 'Table not found'}), 404

    # Check if the player is already seated
    existing = TablePlayer.query.filter_by(user_id=current_user.id, table_id=table_id).first()
    if existing:
        return jsonify({'message': 'Already seated at the table'}), 200

    # Check if table is full
    players_count = TablePlayer.query.filter_by(table_id=table_id).count()
    if players_count >= table.max_players:
        return jsonify({'error': 'Table is full'}), 400

    # Ensure user has chips (default to 1000 if not set)
    chips = current_user.chips if hasattr(current_user, 'chips') and current_user.chips > 0 else 1000

    # Create new TablePlayer entry
    new_player = TablePlayer(
        user_id=current_user.id,
        table_id=table_id,
        chips=chips,
        status='seated'
    )
    db.session.add(new_player)
    db.session.commit()

    # Broadcast to all clients at the table
    # broadcast_players_update(table_id)

    # Return updated list of players
    players = TablePlayer.query.filter_by(table_id=table_id).all()
    players_data = [{
        'user_id': p.user_id,
        'chips': p.chips,
        'status': p.status
    } for p in players]

    return jsonify({
        'message': f'Joined table {table.name} successfully',
        'players': players_data
    }), 200


@table_players_bp.route('/leave_table/<int:table_id>', methods=['POST'])
@login_required
def leave_table(table_id):
    """
    Allows a logged-in user to leave a poker table.
    Deletes their TablePlayer record, commits the change,
    broadcasts an update to other players, and returns confirmation.
    """
    player = TablePlayer.query.filter_by(user_id=current_user.id, table_id=table_id).first()
    if not player:
        return jsonify({'error': 'You are not seated at this table'}), 400

    db.session.delete(player)
    db.session.commit()

    # Broadcast updated player list to others
    broadcast_players_update(table_id)

    return jsonify({'message': f'Left table {table_id} successfully'}), 200
