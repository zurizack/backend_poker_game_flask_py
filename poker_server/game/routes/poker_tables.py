# poker_sever/game/routes/poker_tables.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.poker_server.utils.permissions import admin_required
from backend.poker_server import db
from backend.poker_server.models.poker_table import PokerTable
# from poker_server.game.services.table_service import get_or_create_table_state
from backend.poker_server.sql_services.table_data import get_table_data_from_sql_db

# Create a Blueprint for game-related routes
poker_tables_bp = Blueprint('poker_tables', __name__, url_prefix='/game')

# Route to create a new poker table (accessible only to admin users)
@poker_tables_bp.route('/create_table', methods=['POST'])
@login_required
@admin_required
def create_table():
    data = request.get_json()
    table_name = data.get('table_name')
    max_players = data.get('max_players', 9)
    small_blind = data.get('small_blind')
    big_blind = data.get('big_blind')

    if not table_name:
        return jsonify({'error': 'Table name is required'}), 400
    if small_blind is None or big_blind is None:
        return jsonify({'error': 'Small blind and big blind are required'}), 400

    # Convert blinds to integers and validate input
    try:
        small_blind = int(small_blind)
        big_blind = int(big_blind)
    except (TypeError, ValueError):
        return jsonify({'error': 'Small blind and big blind must be integers'}), 400

    new_table = PokerTable(
        name=table_name,
        max_players=max_players,
        small_blind=small_blind,
        big_blind=big_blind
    )

    # Attempt to save the new table to the database
    try:
        db.session.add(new_table)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

    return jsonify({
        'message': f'Table "{table_name}" created successfully',
        'table': {
            'id': new_table.id,
            'name': new_table.name,
            'max_players': new_table.max_players,
            'small_blind': new_table.small_blind,
            'big_blind': new_table.big_blind
        }
    }), 201

# Route to delete a poker table by its ID (admin only)
@poker_tables_bp.route('/delete_table/<int:table_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_table(table_id):
    table = PokerTable.query.get(table_id)

    if not table:
        return jsonify({'error': 'Table not found'}), 404

    # Attempt to delete the table from the database
    try:
        db.session.delete(table)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

    return jsonify({'message': f'Table "{table.name}" deleted successfully'}), 200

# Route to list all existing poker tables (accessible to authenticated users)
@poker_tables_bp.route('/tables', methods=['GET'])
@login_required
def list_tables():
    tables = PokerTable.query.all()
    tables_data = [
        {
            'id': t.id,
            'name': t.name,
            'max_players': t.max_players,
            'small_blind': t.small_blind,
            'big_blind': t.big_blind
        } for t in tables
    ]
    return jsonify(tables_data), 200

# Route to check the current authentication status and user info
@poker_tables_bp.route('/check_auth')
def check_auth():
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'user_id': getattr(current_user, 'id', None),
        'nickname': getattr(current_user, 'nickname', None),
        'first_name': getattr(current_user, 'first_name', None),
        'last_name': getattr(current_user, 'last_name', None),
        'is_admin': getattr(current_user, 'is_admin', False)
    })

@poker_tables_bp.route('/table/<int:table_id>')
@login_required
def get_table(table_id):
    table_data = get_table_data_from_sql_db(table_id)
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

@poker_tables_bp.route('/<int:table_id>/state', methods=['GET'])
@login_required
def get_table_state_route(table_id):
    state = get_or_create_table_state(table_id)
    return jsonify(state)