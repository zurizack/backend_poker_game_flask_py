# game/engine/showdown.py

from backend.poker_server.utils.poker_hand_evaluator import evaluate_hand_strength
# from poker_server.utils.poker_hand_evaluator import  compare_hands

import logging

def handle_showdown(state):
    community_cards = state.get("community_cards", [])
    players = state.get("players", [])

    active_players = [p for p in players if not p.get("folded", False)]
    hand_strengths = []

    for player in active_players:
        hand = player.get("hand", [])
        if len(hand) != 2:
            continue  # שחקן לא תקין

        full_hand = hand + community_cards
        strength = evaluate_hand_strength(full_hand)
        player["hand_strength"] = strength
        hand_strengths.append((player["player_id"], strength))

    if not hand_strengths:
        return state  # לא אמור לקרות

    # מיון לפי עוצמה מהגבוה לנמוך
    hand_strengths.sort(key=lambda x: x[1], reverse=True)
    best_strength = hand_strengths[0][1]
    winners = [pid for pid, s in hand_strengths if s == best_strength]

    pot = state.get("pot", 0)
    win_amount = pot // len(winners)

    for player in players:
        if player["player_id"] in winners:
            player["chips"] += win_amount
            logging.info(f"Player {player['player_id']} won {win_amount} chips")

    state["winners"] = winners
    state["stage"] = "showdown"
    state["status"] = "hand_over"

    return state
