# poker_server/game/core/action_logic.py
from backend.poker_server.game.core.handlers import _deduct_chips_and_update_pot


def apply_bet(state, player, amount):
    if state.get("call_amount", 0) > 0:
        raise ValueError("Cannot bet after a bet has been made")
    _deduct_chips_and_update_pot(state, player, amount)
    player["chips_in_pot"] = amount
    state["call_amount"] = amount

def apply_raise(state, player, amount):
    call_amount = state.get("call_amount", 0)
    current_bet = player.get("chips_in_pot", 0)
    diff = amount - current_bet

    if diff <= 0:
        raise ValueError("Raise must increase the current bet")

    if diff > player["chips"]:
        raise ValueError("Not enough chips to raise")

    _deduct_chips_and_update_pot(state, player, diff)
    player["chips_in_pot"] = amount
    state["call_amount"] = amount

def apply_call(state, player):
    call_amount = state.get("call_amount", 0)
    diff = call_amount - player.get("chips_in_pot", 0)
    if diff > player["chips"]:
        raise ValueError("Not enough chips to call")
    _deduct_chips_and_update_pot(state, player, diff)
    player["chips_in_pot"] = call_amount

def apply_check(state, player):
    if player.get("chips_in_pot", 0) < state.get("call_amount", 0):
        raise ValueError("Cannot check when you haven’t matched the current bet")

def apply_fold(state, player):
    player["folded"] = True







