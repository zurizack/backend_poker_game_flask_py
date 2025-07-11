import enum
from typing import List, Optional

from poker_server.game.engine.card_oop import Card # Ensure this is the correct import for the Card class

# Define Enum for player hand states
class PlayerHandStatus(enum.Enum):
    """
    Represents the different states of a player in a current poker hand.
    """
    ACTIVE = "ACTIVE"                       # Active, can perform actions
    FOLDED = "FOLDED"                       # Folded the hand, not participating in the pot
    ALL_IN = "ALL_IN"                       # Bet all chips, still participating in the pot
    # A new player who just sat down or a returning player, waiting for the next hand.
    WAITING_FOR_NEW_HAND = "WAITING_FOR_NEW_HAND" 
    # A player sitting at the table but not participating in the current hand (e.g., taking a short break).
    SITTING_OUT = "SITTING_OUT"
    NOT_SEATED = "NOT_SEATED"

# Define Enum for player actions (might already exist elsewhere, but included here for completeness)
class PlayerAction(enum.Enum):
    """
    Represents the possible actions a player can perform.
    """
    CHECK = "CHECK"
    CALL = "CALL"
    RAISE = "RAISE"
    BET = "BET"
    FOLD = "FOLD"
    ALL_IN = "ALL_IN" # Can be an action by itself, or part of BET/RAISE/CALL


class PlayerHand:
    """
    A class that represents the specific hand state of a player within an ongoing poker hand.
    Contains the cards, hand status, current bet in the hand, and last action.
    """
    def __init__(self):
        """
        Constructor for the PlayerHand class.
        Resets all hand data, defaulting to WAITING_FOR_NEW_HAND.
        """
        self._cards: List[Card] = []
        self._status: PlayerHandStatus = PlayerHandStatus.WAITING_FOR_NEW_HAND
        self._current_bet_in_hand: int = 0  # Total chips the player has bet in this hand (across all rounds).
        self._last_action: Optional[PlayerAction] = None

    def set_cards(self, cards: List[Card]):
        """
        Sets the player's hole cards.
        :param cards: A list of two Card objects.
        :raises ValueError: If the list does not contain exactly 2 cards.
        """
        if len(cards) != 2:
            raise ValueError("A poker hand must contain exactly 2 cards.")
        self._cards = list(cards) # Store a copy

    def clear_cards(self):
        """
        Clears the player's hand cards (for a new hand).
        """
        self._cards = []

    def get_cards(self) -> List[Card]:
        """
        Returns a copy of the player's hole cards.
        """
        return list(self._cards) # Returns a copy to prevent direct external modification

    def set_status(self, status: PlayerHandStatus):
        """
        Sets the player's current hand status.
        :param status: One of the PlayerHandStatus values.
        """
        self._status = status

    def get_status(self) -> PlayerHandStatus:
        """
        Returns the player's current hand status.
        """
        return self._status

    def add_to_bet(self, amount: int):
        """
        Adds an amount to the player's accumulated bet in this hand.
        :param amount: The amount to add. Must be positive.
        :raises ValueError: If the amount is negative.
        """
        if amount < 0:
            raise ValueError("Bet amount must be positive.")
        self._current_bet_in_hand += amount

    def get_bet_in_hand(self) -> int:
        """
        Returns the total chips the player has bet in this hand (across all rounds).
        """
        return self._current_bet_in_hand

    def reset_bet(self):
        """
        Resets the accumulated bet amount in the hand (for a new hand).
        """
        self._current_bet_in_hand = 0

    def set_last_action(self, action: PlayerAction):
        """
        Sets the last action performed by the player.
        :param action: One of the PlayerAction values.
        """
        self._last_action = action

    def get_last_action(self) -> Optional[PlayerAction]:
        """
        Returns the last action performed by the player.
        """
        return self._last_action

    def reset_state(self):
        """
        Resets all hand-specific states for the start of a new hand.
        Sets the status to ACTIVE by default for a new hand.
        """
        self.clear_cards()
        self.reset_bet()
        self.set_status(PlayerHandStatus.ACTIVE) # Default: active in a new hand
        self.set_last_action(None)

    def __str__(self) -> str:
        """
        Returns a readable representation of the hand state, for display purposes.
        """
        # No direct Hebrew conversion needed since the Enum values themselves are English.
        # This mapping was for Hebrew display, but for English output, the enum value is sufficient.
        status_display = self.get_status().value
        
        cards_display = ", ".join(str(card) for card in self._cards) if self._cards else "No cards"
        last_action_display = self.get_last_action().value if self.get_last_action() else "None"

        return (
            f"Hand Status: {status_display} "
            f"- Cards: [{cards_display}] "
            f"- Bet in Hand: {self._current_bet_in_hand} "
            f"- Last Action: {last_action_display}"
        )

    def __repr__(self) -> str:
        """
        Returns an unambiguous representation of the object, used for debugging and development.
        """
        cards_repr = [repr(card) for card in self._cards]
        return (
            f"PlayerHand(cards={cards_repr}, status={self._status.value}, "
            f"current_bet_in_hand={self._current_bet_in_hand}, "
            f"last_action={self._last_action.value if self._last_action else 'None'})"
        )
