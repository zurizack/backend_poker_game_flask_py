
# poker_server/game/core/validators.py


def validate_player_action_request(state, player_id, action, amount):
    if action not in {"fold", "call", "raise", "bet", "check"}:
        raise ValueError("Invalid action")

    if state.get("current_turn_player_id") != player_id:
        raise ValueError("Not your turn")

    if action in {"bet", "raise"} and (amount is None or amount <= 0):
        raise ValueError("Invalid amount for action")