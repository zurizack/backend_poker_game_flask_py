# backend/poker_server/game/sockets/handlers/player_take_a_seat_handler.py

import logging
from typing import Dict, Any, Optional
from flask_login import current_user 
from flask_socketio import SocketIO, join_room, leave_room

from backend.poker_server import game_manager_instance 
from backend.poker_server.game.sockets.emitters_oop import PokerEmitters
from backend.poker_server.game.engine.player_oop import Player 
from backend.poker_server.game.engine.table_oop import Table 
from backend.poker_server.models.user import User 

logger = logging.getLogger(__name__)

def handle_player_take_a_seat_request(socketio: SocketIO, player_id: int, sid: str, data: Dict[str, Any]) -> Optional[int]:
    """
    מטפל בבקשת שחקן לתפוס מקום בשולחן.
    :param socketio: מופע ה-SocketIO.
    :param player_id: ה-ID של השחקן (מגיע מהאירוע, אמור להיות זהה ל-current_user.id).
    :param sid: ה-Socket ID של השחקן.
    :param data: מילון המכיל 'table_id', 'seat' ו-'buy_in_amount'.
    :return: ה-ID של השולחן אם ההושבה הצליחה, אחרת None.
    """
    logger.info(f"Handler received seat request: Player ID {player_id}, Table ID {data.get('table_id')}, Seat: {data.get('seat')}, Buy-in: {data.get('buy_in_amount')}.")

    table_id_str = data.get('table_id')
    seat_number = data.get('seat')
    buy_in_amount = data.get('buy_in_amount')

    if not all([table_id_str, seat_number is not None, buy_in_amount is not None]):
        PokerEmitters.emit_error(sid, "Missing table_id, seat, or buy_in_amount for take seat request.")
        logger.error(f"Take seat request from SID {sid} missing required data.")
        return None

    try:
        table_id = str(table_id_str) 
        buy_in_amount = float(buy_in_amount)
        seat_number = int(seat_number)
    except (ValueError, TypeError):
        PokerEmitters.emit_error(sid, "Invalid data format for table ID, seat, or buy-in amount.")
        logger.error(f"Take seat request from SID {sid} has invalid data types.")
        return None

    if not current_user.is_authenticated:
        PokerEmitters.emit_error(sid, "Authentication required to take a seat.")
        logger.error(f"Unauthenticated user (SID: {sid}) tried to take a seat.")
        return None

    if player_id != current_user.id:
        logger.warning(f"Player ID mismatch in take seat request: event {player_id}, current_user {current_user.id}. Using current_user.id.")
        player_id = current_user.id 

    player_obj: Optional[Player] = game_manager_instance.register_or_update_player_connection(current_user, sid)
    
    if not player_obj:
        PokerEmitters.emit_error(sid, "Failed to retrieve or create player object. Internal error.")
        logger.error(f"Could not get or create player object for authenticated user {current_user.id} (SID: {sid}) in take seat handler.")
        return None

    # ✅ קריאה למתודה החדשה ב-GameManager
    success = game_manager_instance.add_player_to_table_as_player(player_obj.user_id, table_id, buy_in_amount, seat_number)

    if success:
        PokerEmitters._emit('seat_success', {'message': f"Successfully took seat {seat_number} at table {table_id}."}, sid=sid)
        # שלח את מצב השולחן המעודכן לכל השחקנים בשולחן
        table = game_manager_instance.get_table_by_id(table_id)
        if table:
            PokerEmitters.emit_full_table_state(sid ,table, requesting_player_id=player_obj.user_id) # העבר את ה-ID של השחקן המבקש
            logger.info(f"Player {player_id} successfully took seat {seat_number} on table {table_id}. Table state broadcasted.")
            return int(table_id) 
        else:
            logger.error(f"Table {table_id} not found after successful seat. This shouldn't happen.")
            return None
    else:
        PokerEmitters.emit_error(sid, "Could not take the requested seat. It might be occupied, insufficient chips, or another error occurred.")
        logger.warning(f"Handler: Failed to seat player {player_id} at seat {seat_number} on table {table_id}.")
        return None
