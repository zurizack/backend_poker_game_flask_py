# poker_server/game/core/turn.py
from backend.poker_server.game.core.utils import (
    get_active_players,
    get_next_seat_after,
    get_next_player_id
)


def advance_turn(table_state, current_player_id):
    """
    Advances the turn to the next active player in the game.
    :param table_state: The current game state dictionary.
    :param current_player_id: The ID of the player whose turn it just was.
    """
    next_player = get_next_player_id(table_state, current_player_id)
    # Set the current_turn_player_id to the next player, or -1 if no next player found
    table_state["current_turn_player_id"] = next_player if next_player is not None else -1


def assign_first_to_act(state):
    """
    Assigns the first player to act for the current betting round based on the game stage.
    Pre-flop: Player after the Big Blind.
    Post-flop (Flop, Turn, River): Player after the Dealer.
    :param state: The current game state dictionary.
    """
    stage = state.get("stage")
    if stage == "pre_flop": # Corrected from "preflop" to "pre_flop" for consistency
        # Start from the player after the Big Blind
        bb_seat = state.get("big_blind_seat")
        next_seat = get_next_seat_after(state, bb_seat)
    else:
        # After flop, start from the player after the Dealer
        dealer_seat = state.get("dealer_position")
        next_seat = get_next_seat_after(state, dealer_seat)

    if next_seat is None:
        # If no next seat found (e.g., only one player left), set to None
        state["current_turn_player_id"] = None
        return

    # Find the active player sitting in that seat
    for p in get_active_players(state):
        if p["seat"] == next_seat:
            state["current_turn_player_id"] = p["player_id"]
            return

    # Fallback: if for some reason the specific player is not active, take the next one
    # This might happen if the player in 'next_seat' folded, for example.
    active = get_active_players(state)
    state["current_turn_player_id"] = active[0]["player_id"] if active else None

