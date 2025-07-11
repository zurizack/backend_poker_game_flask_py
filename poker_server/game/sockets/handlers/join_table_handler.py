# poker_server/game/sockets/handlers/join_table_handler.py

import logging
from typing import Dict, Any, Optional
from flask_socketio import SocketIO, join_room, leave_room
from flask_login import current_user

# Import the global instance of game_manager_instance
from poker_server import game_manager_instance 

from poker_server.game.sockets.emitters_oop import PokerEmitters
from poker_server.game.engine.player_oop import Player

logger = logging.getLogger(__name__)

# Function signature as you specified: game_manager is not a parameter
def handle_join_table_request(socketio: SocketIO, player_id: int, sid: str, data: Dict[str, Any]) -> Optional[str]:
    """
    Handles a player's request to join a table as a viewer.
    :param socketio: The SocketIO instance.
    :param player_id: The player's ID (comes from current_user.id).
    :param sid: The player's Socket ID.
    :param data: A dictionary containing 'table_id'.
    :return: The ID of the table the player successfully joined, otherwise None.
    """
    table_id_str = data.get('table_id')

    logger.info(f"Handler received join table request: Player ID {player_id}, Table ID: {table_id_str}.")

    # 1. Ensure essential data exists
    if not table_id_str:
        PokerEmitters.emit_error(sid, "Missing table ID for join table request.")
        logger.error(f"Join table request from SID {sid} missing table_id.")
        return None

    table_id = str(table_id_str) # Ensure it's a string

    try:
        # 2. Ensure the user is authenticated and update the Player object in GameManager
        if not current_user.is_authenticated:
            PokerEmitters.emit_error(sid, "Authentication required to join a table.")
            logger.error(f"Unauthenticated user (SID: {sid}) tried to join a table.")
            return None
        
        # Ensure the player_id from the event matches the authenticated user's ID.
        if player_id != current_user.id:
            logger.warning(f"Player ID mismatch in join table request: event {player_id}, current_user {current_user.id}. Using current_user.id.")
            player_id = current_user.id # Ensure consistency

        # Use the globally imported instance
        player_obj: Optional[Player] = game_manager_instance.register_or_update_player_connection(current_user, sid)
        
        if not player_obj:
            PokerEmitters.emit_error(sid, "Failed to retrieve or create player object. Internal error.")
            logger.error(f"Could not get or create player object for authenticated user {current_user.id} (SID: {sid}) in join table handler.")
            return None

        # 3. Try to add the player (as a viewer) to the table using GameManager
        # ✅ Call the new method to handle adding a viewer in GameManager
        success = game_manager_instance.add_player_to_table_as_viewer(player_obj.user_id, table_id) 

        if success:
            join_room(table_id) # Join the socket to the specific table room
            logger.info(f"Player {player_id} (SID: {sid}) successfully joined table {table_id} as a viewer.")
            
            # 4. Send the updated table state to the client
            # ✅ Call the new method that will return the full table state (as a dictionary)
            table_state = game_manager_instance.get_table_state(table_id) 
            if table_state:
                # ✅ Use PokerEmitters._emit with an explicit event name
                PokerEmitters._emit('full_table_state', table_state, room=sid) # Changed sid=sid to room=sid to emit only to the specific client
            else:
                logger.error(f"Table {table_id} not found after player {player_id} joined. This shouldn't happen.")
                PokerEmitters.emit_error(sid, "Internal error: Table state not found.")
                return None # Return None if table state not found

            # ✅ Use PokerEmitters._emit with an explicit event name
            PokerEmitters._emit('join_success', {'message': f"Successfully joined table {table_id}."}, room=sid) # Changed sid=sid to room=sid
            return table_id
        else:
            PokerEmitters.emit_error(sid, "Could not join the requested table. It might not exist or another error occurred.")
            logger.warning(f"Handler: Failed to join table {table_id} for player {player_id}.")
            return None

    except Exception as e:
        logger.exception(f"Error handling join table request for player {player_id} (SID: {sid}, Data: {data}): {e}")
        PokerEmitters.emit_error(sid, "An unexpected error occurred while joining the table.")
        return None
