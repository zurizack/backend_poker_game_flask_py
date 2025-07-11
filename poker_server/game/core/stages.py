# poker_server/game/core/stages
from poker_server.game.core.utils import get_next_player_id, get_player_by_id
import logging
from poker_server.game.engine.showdown import handle_showdown
from poker_server.game.core.round import (
    reset_round_state,
    update_stage_state,
    deal_community_cards,
    assign_first_to_act_postflop

)
from poker_server.game.core.turn import assign_first_to_act

STAGES = ["pre_flop", "flop", "turn", "river", "showdown"]

def advance_stage(state):
    """
    Advances the game to the next stage (Flop, Turn, River, or Showdown).
    Resets the betting round state and deals community cards if applicable.
    """
    logging.info(">>> advance_stage called, current stage: %s", state["stage"])

    # Reset betting-round specific state for the new stage
    reset_round_state(state)

    # Update the overall game stage (e.g., from 'pre_flop' to 'flop')
    update_stage_state(state)

    # 💥 Stop for Showdown
    if state["stage"] == "showdown":
        logging.info("🎬 Moving to showdown phase")
        state = handle_showdown(state)
        return state  # No need to continue processing stage logic

    # Deal community cards for the new stage (Flop, Turn, River)
    deal_community_cards(state)

    # Assign the first player to act for the new betting round (post-flop logic)
    assign_first_to_act_postflop(state)
    
    return state

def is_hand_over(state):
    """
    Checks if the entire hand has ended (only one player remaining, or reached showdown).
    :param state: The current game state dictionary.
    :return: True if the hand is over, False otherwise.
    """
    # Active players are those who have not folded and have a player_id
    active = [p for p in state["players"] if not p.get("folded") and p.get("player_id")]

    # If 1 or fewer active players remain, the hand is over (unless it's showdown after all cards are dealt)
    if len(active) <= 1:
        return True

    # If the current stage is 'river' and the betting round is over, the hand is also over (leading to showdown)
    return state.get("current_round") == "river" and is_betting_round_over(state)

def is_betting_round_over(state: dict, current_player_id: int) -> bool:
    """
    Checks if the current betting round has concluded according to poker game logic.
    This function determines if all active players have either called the highest bet,
    gone all-in, or folded, and it's the turn of a player who has already acted
    or the big blind has been called on pre-flop.

    :param state: The current game state dictionary.
    :param current_player_id: The ID of the player whose turn it just was.
    :return: True if the betting round is over, False otherwise.
    """
    stage = state.get("stage")
    players = state.get("players", [])
    call_amount = state.get("call_amount", 0) # The amount needed to call the current highest bet

    current_player = get_player_by_id(current_player_id, players)
    # Get the next player in the betting order
    next_player_id = get_next_player_id(state, current_player_id)
    next_player = get_player_by_id(next_player_id, players)

    # 💡 Pre-flop logic
    if stage == "pre_flop":
        big_blind = state.get("big_blind", 10) # Default Big Blind amount
        # If the call amount matches the big blind, the round ends when it's the Big Blind's turn
        # (meaning the BB has had a chance to check or raise after everyone else called)
        if call_amount == big_blind:
            return current_player and current_player.get("seat") == state.get("big_blind_seat")
        else:
            # If there was a raise, the round ends when the next player has matched the call_amount.
            # This implies all players who haven't folded have matched the highest bet.
            return next_player and next_player.get("chips_in_pot", 0) >= call_amount
    else:
        # 💡 Flop / Turn / River (Post-flop logic)
        # If the call amount is 0 (meaning no bets/raises in this round yet, or all checked)
        # the round ends when it's the dealer's turn (or the first player after the dealer).
        if call_amount == 0:
            return current_player and current_player.get("seat") == state.get("dealer_position")
        else:
            # If there was a bet/raise, the round ends when the next player has matched the call_amount.
            return next_player and next_player.get("chips_in_pot", 0) >= call_amount

