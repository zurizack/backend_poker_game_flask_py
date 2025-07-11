
# poker_sever/game/services/gameplay_service.py

from poker_server.game.core.stages import advance_stage, is_betting_round_over
from poker_server.game.core.turn import advance_turn
from poker_server.game.core.utils import find_player_by_id
from poker_server.game.core.validators import validate_player_action_request
from poker_server.game.core.actions import (
    apply_bet,
    apply_call,
    apply_check,
    apply_fold,
    apply_raise,
    )


def apply_player_action_logic(state, player_id, action, amount=None):
    validate_player_action_request(state, player_id, action, amount)
    player = find_player_by_id(state, player_id)

    action_map = {
        "bet": apply_bet,
        "raise": apply_raise,
        "call": apply_call,
        "check": apply_check,
        "fold": apply_fold
    }

    action_func = action_map.get(action)
    if not action_func:
        raise ValueError("Unsupported action")

    if action in {"bet", "raise"}:
        action_func(state, player, amount)
    else:
        action_func(state, player)

    if is_betting_round_over(state, player_id):
        state = advance_stage(state)

    else:
        advance_turn(state, player_id)

    return state