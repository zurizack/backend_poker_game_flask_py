# game/engine/showdown.py

from backend.poker_server.utils.poker_hand_evaluator import evaluate_hand_strength
# from poker_server.utils.poker_hand_evaluator import compare_hands # This line was commented out in original

import logging

def handle_showdown(state):
    """
    Handles the showdown phase of a poker hand.
    Evaluates the hand strength of all active players, determines winners,
    and distributes the pot.

    :param state: The current game state dictionary.
    :return: The updated game state dictionary.
    """
    community_cards = state.get("community_cards", [])
    players = state.get("players", [])

    # Filter for players who are still active (have not folded)
    active_players = [p for p in players if not p.get("folded", False)]
    hand_strengths = [] # List to store (player_id, hand_strength) tuples

    # Evaluate each active player's hand strength
    for player in active_players:
        hand = player.get("hand", []) # Get player's hole cards
        if len(hand) != 2:
            logging.warning(f"Player {player.get('player_id')} has an invalid number of cards ({len(hand)}). Skipping hand evaluation.")
            continue  # Invalid player, skip

        # Combine player's hand with community cards for evaluation
        full_hand = hand + community_cards
        # Evaluate the strength of the full 7-card hand (or fewer if community cards are not all dealt)
        strength = evaluate_hand_strength(full_hand)
        
        # Store the hand strength directly in the player's dictionary for easy access
        player["hand_strength"] = strength
        hand_strengths.append((player["player_id"], strength))

    if not hand_strengths:
        logging.warning("No active players with valid hands for showdown. Returning state as is.")
        return state  # Should not happen in a typical game flow if at least one player is active

    # Sort players by hand strength from highest to lowest
    hand_strengths.sort(key=lambda x: x[1], reverse=True)
    
    # Determine the best hand strength
    best_strength = hand_strengths[0][1]
    # Identify all players who have the best hand strength (for ties)
    winners = [pid for pid, s in hand_strengths if s == best_strength]

    # Get the total pot size
    pot = state.get("pot", 0)
    
    # Calculate the winning amount per winner (split pot if multiple winners)
    win_amount = pot // len(winners)

    # Distribute winnings to the winners
    for player in players:
        if player["player_id"] in winners:
            # Add the winning amount to the player's chips
            player["chips"] += win_amount
            logging.info(f"Player {player['player_id']} won {win_amount} chips in showdown.")
        else:
            # For non-winners, ensure their chips are not affected (they lost their bet)
            pass # No action needed for losers here, their chips were already moved to pot

    # Update the game state with winners and hand status
    state["winners"] = winners
    state["stage"] = "showdown"
    state["status"] = "hand_over" # Indicate that the hand has concluded

    return state
