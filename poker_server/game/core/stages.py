# oker_server/game/core/stages
from backend.poker_server.game.core.utils import get_next_player_id, get_player_by_id
import logging
from backend.poker_server.game.engine.showdown import handle_showdown
from backend.poker_server.game.core.round import (
    reset_round_state,
    update_stage_state,
    deal_community_cards,
    assign_first_to_act_postflop

)
from backend.poker_server.game.core.turn import assign_first_to_act

STAGES = ["pre_flop", "flop", "turn", "river", "showdown"]

def advance_stage(state):

    logging.info(">>> advance_stage called, current stage: %s", state["stage"])

    
    reset_round_state(state)

    update_stage_state(state)

        # 💥 עצירה לשואו דאון
    if state["stage"] == "showdown":
        logging.info("🎬 Moving to showdown phase")
        state = handle_showdown(state)
        return state  # אין טעם להמשיך

    deal_community_cards(state)

    assign_first_to_act_postflop(state)
    
    return state

def is_hand_over(state):

    """
    בודקת אם היד כולה הסתיימה (נשאר רק שחקן אחד, או שהגענו לשואודאון).
    """
    active = [p for p in state["players"] if not p.get("folded") and p.get("player_id")]

    if len(active) <= 1:
        return True

    return state.get("current_round") == "river" and is_betting_round_over(state)

def is_betting_round_over(state: dict, current_player_id: int) -> bool:

    """
    בודק האם סיבוב ההימורים הנוכחי הסתיים בהתאם ללוגיקת המשחק בפוקר.
    """
    stage = state.get("stage")
    players = state.get("players", [])
    call_amount = state.get("call_amount", 0)

    current_player = get_player_by_id(current_player_id,players)
    next_player_id = get_next_player_id(state, current_player_id)
    next_player = get_player_by_id(next_player_id,players)

    # 💡 Pre-flop logic
    if stage == "pre_flop":
        big_blind = state.get("big_blind", 10)
        if call_amount == big_blind:
            return current_player.get("seat") == state.get("big_blind_seat")
        else:
            return next_player and next_player.get("chips_in_pot", 0) >= call_amount
    else:
        # 💡 Flop / Turn / River
        if call_amount == 0:
            return current_player.get("seat") == state.get("dealer_position")
        else:
            return next_player and next_player.get("chips_in_pot", 0) >= call_amount