import logging
from typing import Dict, Any, Optional, List
from flask_socketio import SocketIO, join_room
from ..engine.table_oop import Table
from ..engine.player_oop import Player
from ..engine.card_oop import Card # We will need this if we send cards

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Info level logs
# Can be changed to DEBUG for more detailed development: logger.setLevel(logging.DEBUG)


class PokerEmitters:
    """
    A class that contains all the server's emission (emit) functions.
    Initialized with the main SocketIO instance.
    """
    _socketio_instance: Optional[SocketIO] = None

    @classmethod
    def initialize(cls, socketio_ref: SocketIO):
        """
        Initializes the Emitters class with the main SocketIO instance.
        Called once in app.py during server initialization.
        """
        cls._socketio_instance = socketio_ref
        logger.info("PokerEmitters initialized with SocketIO instance.")

    @classmethod
    def _emit(cls, event_name: str, data: Dict[str, Any], room: Optional[str] = None, sid: Optional[str] = None):
        """
        Internal helper function to perform the actual emission.
        It accepts a room or sid, and emits accordingly.
        """
        if not cls._socketio_instance:
            logger.error(f"Emitters: SocketIO instance not initialized. Cannot emit event '{event_name}'.")
            return

        if room:
            cls._socketio_instance.emit(event_name, data, room=room)
            logger.debug(f"Emitters: Emitted '{event_name}' to room '{room}' with data: {data}")
        elif sid:
            cls._socketio_instance.emit(event_name, data, to=sid) # Using to=sid is preferred over room=sid for a single client
            logger.debug(f"Emitters: Emitted '{event_name}' to SID '{sid}' with data: {data}")
        else:
            # If no room or SID, assume it's a general broadcast to all connections (less common in table-specific games)
            cls._socketio_instance.emit(event_name, data)
            logger.debug(f"Emitters: Emitted '{event_name}' globally with data: {data}")

    # --- General emission functions ---

    @classmethod
    def emit_error(cls, sid: str, message: str):
        """
        Emits an error message to a specific client.
        Event: 'error'
        Data: {"message": "..."}
        """
        logger.warning(f"Emitting error to SID {sid}: {message}")
        cls._emit('error', {"message": message}, sid=sid)

    @classmethod
    def emit_join_success(cls, sid: str, table_id: str, role: str, message: str):
        """
        Emits a success message about joining a table to a specific client.
        Event: 'join_success'
        Data: {"table_id": "...", "role": "...", "message": "..."}
        """
        logger.info(f"Emitting join_success to SID {sid} for table {table_id} as {role}.")
        cls._emit('join_success', {'table_id': table_id, 'role': role, 'message': message}, sid=sid)
        
        # Important: Here we add the SID to the table's room!
        # The SID needs to join a specific room for the table so it can receive updates for the entire room.
        # SocketIO provides the join_room function
        if cls._socketio_instance and sid: # Ensure sid is not None before use
            join_room(str(table_id), sid=sid) # room_name, sid
            logger.debug(f"SID {sid} joined table room {table_id}.")

    @classmethod # Added @classmethod decorator
    def emit_player_seated_success(cls, sid: str, table_id: str, seat_number: int, message: str):
        logger.info(f"Emitting seat_success to SID {sid} for table {table_id} and seat {seat_number}.")
        cls._emit('seat_success', {'table_id': table_id, 'seat_number': seat_number, 'message': message}, sid=sid)
        if cls._socketio_instance and sid: # Ensure sid is not None before use
            join_room(str(table_id), sid=sid) # room_name, sid
            logger.debug(f"SID {sid} joined table room {table_id}.")
            
    # --- Full table state emission functions ---

    @classmethod
    def emit_full_table_state(cls, target_sid: str, table_obj: Table, requesting_player_id: Optional[str] = None):
        """
        Sends the entire table state to a specific client.
        Player-specific data (like hand cards) are tailored to the requesting client.
        Event: 'full_table_state'
        Data: Dictionary of the entire table state.
        """
        logger.info(f"Emitting full_table_state to SID: {target_sid}. Requesting player: {requesting_player_id}")
        
        # Creating the table state dictionary
        # The assumption is that table_obj has a to_dict method that accepts requesting_player_id
        # and reveals private cards only to the requesting player.
        table_state_data = table_obj.to_dict(requesting_player_id=requesting_player_id)
        
        cls._emit('full_table_state', table_state_data, sid=target_sid)
        logger.debug(f"Full table state emitted to SID {target_sid}.")

    @classmethod
    def emit_full_table_state_to_room(cls, table_id: str, table_obj: Table):
        """
        Sends the full public game state (without private hand cards) to all clients in the table room.
        Suitable for spectators or general state initialization.
        Event: 'full_table_state_public'
        Data: Dictionary of the table state (public).
        """
        logger.info(f"Emitting full_table_state_public to room: {table_id}.")
        public_table_state = table_obj.to_dict(requesting_player_id=None) # Important: No requesting player ID
        cls._emit('full_table_state_public', public_table_state, room=str(table_id))
        logger.debug(f"Full public table state emitted to room {table_id}.")

    # --- Partial update emission functions (specific events) ---

    @classmethod
    def emit_player_seated(cls, table_id: str, player_info: Dict[str, Any]):
        """
        Emits when a player has taken a seat at the table.
        Event: 'player_seated'
        Data: {"player_id": "...", "username": "...", "seat_number": ..., "chips": ...}
        """
        logger.info(f"Emitting player_seated for table {table_id}: {player_info['username']} at seat {player_info['seat_number']}.")
        cls._emit('player_seated', player_info, room=str(table_id))

    @classmethod
    def emit_player_left(cls, table_id: str, player_id: str, seat_number: int):
        """
        Emits when a player has left the table.
        Event: 'player_left'
        Data: {"player_id": "...", "seat_number": ...}
        """
        logger.info(f"Emitting player_left for table {table_id}: player {player_id} from seat {seat_number}.")
        cls._emit('player_left', {"player_id": player_id, "seat_number": seat_number}, room=str(table_id))

    @classmethod
    def emit_hand_started(cls, table_id: str, hand_number: int, dealer_seat: int, small_blind_amount: int, big_blind_amount: int):
        """
        Emits when a new poker hand starts.
        Event: 'hand_started'
        Data: {"hand_number": ..., "dealer_seat": ..., "small_blind_amount": ..., "big_blind_amount": ...}
        """
        logger.info(f"Emitting hand_started for table {table_id}: Hand #{hand_number}, Dealer: {dealer_seat}.")
        cls._emit('hand_started', {
            "hand_number": hand_number,
            "dealer_seat": dealer_seat,
            "small_blind_amount": small_blind_amount,
            "big_blind_amount": big_blind_amount
        }, room=str(table_id))

    @classmethod
    def emit_player_cards_dealt(cls, sid: str, hand_cards: List[Dict[str, Any]]):
        """
        Emits the specific hand cards to a player.
        Event: 'your_cards'
        Data: {"cards": [{"rank": "...", "suit": "..."}, ...]}
        """
        logger.info(f"Emitting player_cards_dealt to SID {sid}.")
        # hand_cards is expected to be a list of dictionaries representing cards, for example:
        # [{"rank": card.rank.value, "suit": card.suit.value} for card in player_hand_cards]
        cls._emit('your_cards', {"cards": hand_cards}, sid=sid)
        
    @classmethod
    def emit_player_acted(
        cls,
        table_id: str,
        player_id: str,
        action_type: str, # 'fold', 'check', 'call', 'bet', 'raise'
        amount: int,      # The amount the player put in (for call/bet/raise)
        current_bet_in_round: int, # The total amount the player has bet in the current round
        player_chips_on_table: int, # The player's remaining chips on the table
        pot_size: int, # The total pot size after the action
        next_player_to_act_seat: Optional[int] = None, # The seat of the next player to act (if known)
        next_player_call_amount: Optional[int] = None # The amount to call for the next player (if known)
    ):
        """
        Emits an update about a player's action to all clients in the table room.
        This is a more detailed event that combines 'player_action_update' from the original code.
        Event: 'player_acted'
        Data: {"player_id": "...", "action_type": "...", "amount": ..., "current_bet_in_round": ...,
              "player_chips_on_table": ..., "pot_size": ..., "next_player_to_act_seat": ...,
              "next_player_call_amount": ...}
        """
        action_data = {
            "player_id": player_id,
            "action_type": action_type,
            "amount": amount,
            "current_bet_in_round": current_bet_in_round,
            "player_chips_on_table": player_chips_on_table,
            "pot_size": pot_size,
            "next_player_to_act_seat": next_player_to_act_seat,
            "next_player_call_amount": next_player_call_amount
        }
        logger.info(f"Emitting player_acted for table {table_id}: {player_id} {action_type} {amount}.")
        cls._emit('player_acted', action_data, room=str(table_id))

    @classmethod
    def emit_community_cards_updated(cls, table_id: str, new_cards: List[Dict[str, Any]], phase: str):
        """
        Emits when new community cards are revealed (Flop, Turn, River).
        Event: 'community_cards_updated'
        Data: {"cards": [{"rank": "...", "suit": "..."}, ...], "phase": "flop"|"turn"|"river"}
        """
        logger.info(f"Emitting community_cards_updated for table {table_id} (phase: {phase}). Cards: {new_cards}")
        cls._emit('community_cards_updated', {"cards": new_cards, "phase": phase}, room=str(table_id))

    @classmethod
    def emit_pot_size_update(cls, table_id: str, new_pot_size: int):
        """
        Emits an update on the pot size.
        This can be called after collecting blinds or after a betting round.
        Event: 'pot_size_update'
        Data: {"pot_size": ...}
        """
        logger.info(f"Emitting pot_size_update for table {table_id}. New size: {new_pot_size}.")
        cls._emit('pot_size_update', {"pot_size": new_pot_size}, room=str(table_id))

    @classmethod
    def emit_betting_round_started(cls, table_id: str, round_name: str, current_player_seat: int, call_amount: int):
        """
        Emits when a new betting round starts.
        Event: 'betting_round_started'
        Data: {"round_name": "...", "current_player_seat": ..., "call_amount": ...}
        """
        logger.info(f"Emitting betting_round_started for table {table_id}: {round_name}, First to act: {current_player_seat}.")
        cls._emit('betting_round_started', {
            "round_name": round_name,
            "current_player_seat": current_player_seat,
            "call_amount": call_amount
        }, room=str(table_id))
        
    @classmethod
    def emit_betting_round_ended(cls, table_id: str, final_pot_size_for_round: int):
        """
        Emits when a betting round has ended.
        Event: 'betting_round_ended'
        Data: {"final_pot_size": ...}
        """
        logger.info(f"Emitting betting_round_ended for table {table_id}. Pot collected: {final_pot_size_for_round}.")
        cls._emit('betting_round_ended', {"final_pot_size": final_pot_size_for_round}, room=str(table_id))

    @classmethod
    def emit_hand_ended(cls, table_id: str, winners_info: List[Dict[str, Any]], pot_breakdown: List[Dict[str, Any]]):
        """
        Emits when a hand ends, with winner details and pot breakdown.
        Event: 'hand_ended'
        Data: {"winners": [...], "pot_breakdown": [...]}
        winners_info: [{"player_id": "...", "username": "...", "seat_number": ..., "winnings": ..., "hand_rank": "...", "best_five_cards": [...]}, ...]
        pot_breakdown: [{"pot_type": "main"|"side", "amount": ..., "winners": [...]}, ...]
        """
        logger.info(f"Emitting hand_ended for table {table_id}. Winners: {winners_info}.")
        cls._emit('hand_ended', {
            "winners": winners_info,
            "pot_breakdown": pot_breakdown # This will require logic in the Pot class
        }, room=str(table_id))

    @classmethod
    def emit_game_over(cls, table_id: str, message: str):
        """
        Emits when the game at the table ends (e.g., not enough players with chips).
        Event: 'game_over'
        Data: {"message": "..."}
        """
        logger.info(f"Emitting game_over for table {table_id}: {message}.")
        cls._emit('game_over', {"message": message}, room=str(table_id))
