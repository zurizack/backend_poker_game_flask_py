# poker_server/game/core/round.py
import logging
import random
from backend.poker_server.game.engine.card_deck import create_deck, shuffle,deal
from backend.poker_server.game.core.handlers import _deduct_chips_and_update_pot
from backend.poker_server.game.core.turn import assign_first_to_act
from backend.poker_server.game.core.utils import (
    get_active_players,
    get_next_seat_after,
)




def start_new_hand(state):

    try:
        reset_hand(state)
    except Exception as e:
        logging.error(f"Failed to reset hand state: {e}")
        raise

    try:
        reset_players_for_new_hand(state)
    except Exception as e:
        logging.error(f"Failed to reset players: {e}")
        raise

    try:
        assign_next_dealer(state)
    except Exception as e:
        logging.error(f"Failed to assign dealer: {e}")
        raise

    try:
        assign_blind_positions(state)
    except Exception as e:
        logging.error(f"Failed to assign blind positions: {e}")
        raise

    try:
        post_blinds(state)
    except Exception as e:
        logging.error(f"Failed to post blind: {e}")
        raise

    try:
        deal_hands(state)
    except Exception as e:
        logging.error(f"failed to deal hands to player")
        raise


    try:
        assign_first_to_act(state)
    except Exception as e:
        logging.error(f"Failed to assign first to act: {e}")
        raise

    state["stage"] = "pre_flop"
    state["status"] = "in_round"
    return state

def reset_hand(state):
    state["pot"] = 0
    state["call_amount"] = 0
    state["community_cards"] = []
    state["stage"] = "pre_flop"
    state["current_turn_player_id"] = None
    state["deck"] = create_deck()

def assign_next_dealer(state):
    players = [p for p in state["players"] if p.get("player_id")]
    if not players:
        return
    current = state.get("dealer_position")
    seats = sorted([p["seat"] for p in players])
    if current is None:
        state["dealer_position"] = random.choice(seats)
    else:
        state["dealer_position"] = get_next_seat_after(state, current)

def assign_blind_positions(state):
    active_players = get_active_players(state)
    if len(active_players) < 2:
        raise ValueError("Not enough players to assign blinds")

    dealer_seat = state["dealer_position"]
    sb_seat = get_next_seat_after(state, dealer_seat)
    bb_seat = get_next_seat_after(state, sb_seat)

    state["small_blind_seat"] = sb_seat
    state["big_blind_seat"] = bb_seat

def post_blinds(state):
    sb_seat = state.get("small_blind_seat")
    bb_seat = state.get("big_blind_seat")
    sb_amount = state.get("small_blind", 5)
    bb_amount = state.get("big_blind", 10)

    for p in get_active_players(state):
        if p["seat"] == sb_seat:
            _deduct_chips_and_update_pot(state, p, sb_amount)
            p["current_bet"] = sb_amount
            p["chips_in_pot"] = sb_amount
        elif p["seat"] == bb_seat:
            _deduct_chips_and_update_pot(state, p, bb_amount)
            p["current_bet"] = bb_amount
            p["chips_in_pot"] = bb_amount

    state["call_amount"] = bb_amount

def reset_players_for_new_hand(state):
    for player in state["players"]:
        if not player.get("player_id"):
            continue

        # אפס נתוני יד
        player["chips_in_pot"] = 0
        player["current_bet"] = 0
        player["folded"] = False

        # תוכל להוסיף עוד שדות אם אתה שומר קלפים או סטטוסי יד
        player.pop("hole_cards", None)
        player.pop("has_acted", None)

def deal_hands(state):
    
    shuffle(state["deck"])
    for p in state["players"]:
        if p.get("player_id"):
            p["folded"] = False
            p["hand"] = deal(state["deck"], 2)






# def start_round(state):
#     logging.info(f"Starting round at table {state['name']}")

#     try:
#         reset_round_state(state)
#     except Exception as e:
#         logging.error(f"Failed to reset round state: {e}")
#         raise

#     try:
#         prepare_players_for_round(state)
#     except Exception as e:
#         logging.error(f"Failed to prepare players for round: {e}")
#         raise

#     try:
#         assign_dealer_and_blinds(state)
#     except Exception as e:
#         logging.error(f"Failed to assign dealer and blinds: {e}")
#         raise

#     try:
#         post_blinds(state)
#     except Exception as e:
#         logging.error(f"Failed to post blinds: {e}")
#         raise

#     try:
#         assign_first_to_act(state)
#     except Exception as e:
#         logging.error(f"Failed to assign first turn: {e}")
#         raise

#     state["status"] = "in_round"
#     logging.info(f"Round setup complete: Dealer at seat {state['dealer_position']}")
#     return state

def reset_round_state(state):

    """
    Reset players' state for a new betting round.
    This includes clearing current bets (but not total chips in pot),
    and resetting turn status.
    """
    for player in state.get("players", []):
        if player.get("player_id"):
            player["current_bet"] = 0
            player["chips_in_pot"] = 0
    
    state.update({
        "call_amount": 0,
        "current_turn_player_id": None
    })

def update_stage_state(state):
    next_stage = {
        "pre_flop": "flop",
        "flop": "turn",
        "turn": "river",
        "river": "showdown"
    }
    current = state.get("stage")
    state["stage"] = next_stage.get(current, current)

def assign_first_to_act_postflop(state):
    sb_seat = state.get("small_blind_seat")
    if sb_seat is None:
        raise ValueError("Small blind seat not set")

    active_players = get_active_players(state)
    if not active_players:
        state["current_turn_player_id"] = None
        return

    # נתחיל מהסמול בליינד ונחפש את הראשון שמופיע ברשימת הפעילים
    seat = sb_seat
    for _ in range(len(state["players"])):
        for player in active_players:
            if player["seat"] == seat:
                state["current_turn_player_id"] = player["player_id"]
                return
        seat = get_next_seat_after(state, seat)

    # fallback – אם לא נמצא אף אחד, ננקה
    state["current_turn_player_id"] = None

def deal_community_cards(state):

    if state["stage"] == "flop":
        state["community_cards"] = deal(state["deck"],3)
    elif state["stage"] == "turn":
        state["community_cards"] += deal(state["deck"],1)
    elif state["stage"] == "river":
        state["community_cards"] += deal(state["deck"],1)
    elif state["stage"] == "showdown":
        handle_showdown(state)
        return state





def get_public_state(state, table_id):

    from backend.poker_server import db
    from backend.poker_server.models.poker_table import PokerTable

    return {

        "pot": state.get("pot", 0),
        "stage": state.get("stage"),
        "community_cards": state.get("community_cards", []),
        "call_amount": state.get("call_amount", 0),
        "current_turn_player_id": state.get("current_turn_player_id"),
        "dealer_position": state.get("dealer_position"),
        "small_blind_seat": state.get("small_blind_seat"),
        "big_blind_seat": state.get("big_blind_seat"),
        "small_blind": state.get("small_blind"),
        "big_blind": state.get("big_blind"),
        "players": [
            {
                "player_id": p.get("player_id"),
                "nickname": p.get("nickname"),
                "chips": p.get("chips"),
                "folded": p.get("folded", False),
                "seat": p.get("seat"),
                "chips_in_pot": p.get("chips_in_pot", 0),
                "current_bet": p.get("current_bet", 0),
            }
            for p in state["players"]
        ],
    }






