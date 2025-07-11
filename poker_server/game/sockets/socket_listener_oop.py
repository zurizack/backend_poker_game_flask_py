# backend/poker_server/game/sockets/socket_listener_oop.py

import logging
from flask_socketio import join_room
from flask_login import current_user
from flask import request
from typing import Dict, Any
from backend.poker_server.game.sockets.emitters_oop import PokerEmitters
from backend.poker_server.game.sockets.handlers.join_table_handler import handle_join_table_request
from backend.poker_server.game.sockets.handlers.player_take_a_seat_handler import handle_player_take_a_seat_request

from backend.poker_server import game_manager_instance
from backend.poker_server.game.sockets.emitters_oop import PokerEmitters


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def register_handlers_oop(socketio):

    @socketio.on("connect")
    def on_connect():
        # Log: Shows who is connected and with which SID.
        logger.info(f"*** CLIENT CONNECTED *** SID: {request.sid}. Current User Authenticated (Flask-Login): {current_user.is_authenticated}")

        # **Main Authentication Step Here:**
        # We check if the user is authenticated via Flask-Login.
        # If not authenticated, we log a warning and disconnect their connection.
        if not current_user.is_authenticated:
            logger.warning(f"Unauthenticated client {request.sid} attempted to connect. Disconnecting.")
            return False # Returning False disconnects the Socket.IO connection.

        # If we reached here, the user is authenticated.
        player_id = current_user.id
        logger.info(f"Authenticated user {player_id} (SID: {request.sid}) connected.")

        # ✅ לוגיקה לטיפול בהתחברות מחדש של שחקן יושב
        player_obj = game_manager_instance.get_player_by_user_id(player_id)
        if player_obj:
            # עדכן את ה-socket_id של השחקן הקיים
            player_obj.socket_id = request.sid
            game_manager_instance.update_player_socket_id(player_id, request.sid)
            game_manager_instance.mark_player_reconnected(player_id) # סמן כמחובר מחדש

            if player_obj.is_seated():
                table_id = player_obj.table_id
                join_room(str(table_id)) # צרף מחדש לחדר הסוקט
                logger.info(f"Reconnected player {player_id} (SID: {request.sid}) rejoined table {table_id} SocketIO room.")
                
                table_state = game_manager_instance.get_table_state(table_id)
                if table_state:
                    PokerEmitters._emit('full_table_state', table_state, sid=request.sid)
                    PokerEmitters._emit('join_success', {'message': f"Already seated at table {table_id}."}, sid=request.sid)
                else:
                    PokerEmitters.emit_error(request.sid, "Internal error: Table state not found for seated player on reconnect.")
                return # סיים את הטיפול כאן

        # **Very Important:**
        # Do not add lines like join_room here. This caused timing issues in the past.
        # Joining rooms is now handled only within handle_join_table_request.

    @socketio.on('disconnect')
    def on_disconnect():
        logger.info(f"Client disconnected: {request.sid}. Attempting to remove from tables.")
        # Disconnection logic - still requires completion
        player_id_to_disconnect = game_manager_instance.get_player_id_by_socket_id(request.sid) 
        if player_id_to_disconnect:
            logger.info(f"Player {player_id_to_disconnect} (SID: {request.sid}) disconnected.")
            game_manager_instance.mark_player_disconnected(player_id_to_disconnect) 
        else:
            logger.debug(f"Disconnected SID {request.sid} not associated with an active player.")


    @socketio.on("join_table")
    def on_join_table(data: Dict[str, Any]):
        player_id = current_user.id # ✅ השתמש ב-int ישירות
        sid = request.sid # The SID of the current client
        table_id_str = data.get('table_id') # קבל את ה-table_id מוקדם

        logger.info(f"SocketListener: Player {player_id} (SID: {sid}) requested to join table with data: {data}")
        
        # ✅ לוגיקה לטיפול בשחקן שיושב כבר ב-join_table
        player_obj = game_manager_instance.get_player_by_user_id(player_id)
        if player_obj and player_obj.is_seated() and player_obj.table_id == table_id_str:
            logger.info(f"Player {player_id} (SID: {sid}) is already seated at table {table_id_str}. Sending full state directly.")
            join_room(table_id_str) # ודא שהם בחדר
            table_state = game_manager_instance.get_table_state(table_id_str)
            if table_state:
                PokerEmitters._emit('full_table_state', table_state, sid=sid)
                PokerEmitters._emit('join_success', {'message': f"Already seated at table {table_id_str}."}, sid=sid)
            else:
                PokerEmitters.emit_error(sid, "Internal error: Table state not found for seated player.")
            return # סיים את הטיפול כאן

        # Simply call the logic function and pass it the data
        # The logic function will return the table_id if the join was successful, otherwise None
        table_id = handle_join_table_request(socketio, player_id, sid, data)

        # If the join was successful (i.e., we received a table_id), the listener is responsible for joining the SID to the table's Socket.IO room
        if table_id:
            join_room(table_id)
            logger.info(f"SocketListener: Player {player_id} (SID: {sid}) joined SocketIO room {table_id}.")
        
    @socketio.on("player_take_a_seat")
    def on_player_take_a_seat(data: Dict[str, Any]):
        """
        The listener function for the 'player_take_a_seat' event from the client.
        It is responsible for extracting the data and passing it to the handler function.
        """
        if not current_user.is_authenticated:
            logger.warning(f"SocketListener: Unauthenticated user attempted to take a seat.")
            return # Or send an appropriate error message

        # player_id and sid come directly from the Socket.IO session/request
        player_id = current_user.id # ✅ השתמש ב-int ישירות
        sid = request.sid 

        logger.info(f"SocketListener (Listener): Player {player_id} (SID: {sid}) requested to take a seat with data: {data}")
        
        # 🚀 Call the handler function and pass it all relevant data
        # The handler will return the table_id if seating was successful, otherwise None
        table_id = handle_player_take_a_seat_request(socketio, player_id, sid, data)

        # If seating was successful (i.e., we received a table_id back), the listener is responsible for joining the SID to the table's Socket.IO room
        if table_id:
            join_room(table_id)
            logger.info(f"SocketListener (Listener): Player {player_id} (SID: {sid}) joined SocketIO room: {table_id}.")
