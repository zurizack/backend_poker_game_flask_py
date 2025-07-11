# poker_server/game/core/utils.py


def get_player_by_id(player_id,players_list):
    for p in players_list:
        if p["player_id"] == player_id:
            return p
    return None

def get_next_player_id(table_state: dict, current_player_id: int) -> int:

    """
    Returns the player_id of the next active player who has not folded.
    If no active players remain or the current player is not found, returns None.
    """
    players = table_state["players"]
    active_players = [p for p in players if p["player_id"] is not None and not p.get("folded", False)]
    if not active_players:
        return None

    try:
        idx = next(i for i, p in enumerate(active_players) if p["player_id"] == current_player_id)
    except StopIteration:
        return None

    next_idx = (idx + 1) % len(active_players)
    return active_players[next_idx]["player_id"]

def get_active_players(state):
    return [
        p for p in state["players"]
        if p.get("player_id") and not p.get("folded", False) and p.get("chips", 0) > 0
    ]

def get_next_seat_after(state, from_seat):
    players = state["players"]
    seat_numbers = [p["seat"] for p in players if p.get("player_id")]

    if not seat_numbers:
        return None

    sorted_seats = sorted(seat_numbers)
    for seat in sorted_seats:
        if seat > from_seat:
            return seat

    return sorted_seats[0]

def find_player_by_id(state, player_id):

    for p in state["players"]:
        if p["player_id"] == player_id:
            return p
    raise ValueError("Player not found at table")




