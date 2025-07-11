
# poker_server/game/core/handlers.py


def _deduct_chips_and_update_pot(state, player, amount):

    if amount > player["chips"]:
        raise ValueError("Not enough chips")
    player["chips"] -= amount
    player["chips_in_pot"] = player.get("chips_in_pot", 0) + amount
    state["pot"] = state.get("pot", 0) + amount