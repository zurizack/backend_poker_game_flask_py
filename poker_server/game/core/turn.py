# poker_server/game/core/turn.py
from backend.poker_server.game.core.utils import (
    get_active_players,
    get_next_seat_after,
    get_next_player_id
)


def advance_turn(table_state, current_player_id):
    next_player = get_next_player_id(table_state, current_player_id)
    table_state["current_turn_player_id"] = next_player if next_player is not None else -1


def assign_first_to_act(state):
    stage = state.get("stage")
    if stage == "preflop":
        # מתחילים מהשחקן שאחרי הביג בליינד
        bb_seat = state.get("big_blind_seat")
        next_seat = get_next_seat_after(state, bb_seat)
    else:
        # אחרי פלופ מתחילים מהשחקן שאחרי הדילר
        dealer_seat = state.get("dealer_position")
        next_seat = get_next_seat_after(state, dealer_seat)

    if next_seat is None:
        state["current_turn_player_id"] = None
        return

    # מצא את השחקן הפעיל שיושב במקום הזה
    for p in get_active_players(state):
        if p["seat"] == next_seat:
            state["current_turn_player_id"] = p["player_id"]
            return

    # fallback: אם משום מה השחקן הספציפי לא פעיל, קח את הבא בתור
    active = get_active_players(state)
    state["current_turn_player_id"] = active[0]["player_id"] if active else None


















