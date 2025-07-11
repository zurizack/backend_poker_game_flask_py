from typing import Dict


class Card:
    """
    A class that represents a single card in a deck of cards.
    The internal representation is compact (one character for rank and one for suit),
    but it can be displayed in a user-friendly format.
    """

    # Short and common representations for ranks and suits
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    SUITS = ['C', 'D', 'H', 'S']

    # Dictionaries for mapping short representations to readable names and symbols (for display)
    _FULL_RANK_NAMES = {
        'T': "10",
        'J': "Jack",
        'Q': "Queen",
        'K': "King",
        'A': "Ace"
    }
    _FULL_SUIT_NAMES = {
        'C': "Clubs",
        'D': "Diamonds",
        'H': "Hearts",
        'S': "Spades"
    }
    _SUIT_SYMBOLS = {
        'C': "♣",
        'D': "♦",
        'H': "♥",
        'S': "♠"
    }

    def __init__(self, rank: str, suit: str):
        """
        Constructor for the Card class.

        :param rank: The rank of the card (a single character from RANKS).
        :param suit: The suit of the card (a single character from SUITS).
        :raises ValueError: If the rank or suit is invalid.
        """
        if rank not in Card.RANKS:
            raise ValueError(f"Invalid card rank. Valid ranks are: {', '.join(Card.RANKS)}")
        if suit not in Card.SUITS:
            raise ValueError(f"Invalid card suit. Valid suits are: {', '.join(Card.SUITS)}")

        self._rank = rank
        self._suit = suit

    def get_rank(self) -> str:
        """
        Returns the rank of the card in its short representation.
        """
        return self._rank

    def get_suit(self) -> str:
        """
        Returns the suit of the card in its short representation.
        """
        return self._suit

    def get_rank_value(self) -> int:
        """
        Returns the numerical value of the card's rank.
        Used for logical comparisons (e.g., 2 < 3, K > Q).
        """
        return Card.RANKS.index(self._rank) # Index in RANKS list gives numerical value
    
    def to_dict(self) -> Dict[str, str]:
        """
        Converts the card to a dictionary that can be transmitted via Socket.IO.
        """
        return {
            "rank": self._rank,
            "suit": self._suit
        }

    def __str__(self) -> str:
        """
        Returns a readable representation of the card (e.g., "Ace of Spades").
        """
        rank_display = Card._FULL_RANK_NAMES.get(self._rank, self._rank)
        full_suit_name = Card._FULL_SUIT_NAMES.get(self._suit, self._suit)
        suit_symbol = Card._SUIT_SYMBOLS.get(self._suit, self._suit)

        # Choose a format that combines the full name with a symbol, e.g.: "Ace of Spades (♠)"
        return f"{rank_display} of {full_suit_name} ({suit_symbol})"

    def __repr__(self) -> str:
        """
        Returns an unambiguous representation of the object, used for debugging.
        """
        return f"Card(rank='{self._rank}', suit='{self._suit}')"

    def __eq__(self, other) -> bool:
        """
        Allows equality comparison between two Card objects.
        Two cards are considered equal if they have the same rank and suit.
        """
        if not isinstance(other, Card):
            return NotImplemented
        return self._rank == other._rank and self._suit == other._suit

    def __lt__(self, other) -> bool:
        """
        Allows "less than" comparison between two cards, by rank only.
        """
        if not isinstance(other, Card):
            return NotImplemented
        return self.get_rank_value() < other.get_rank_value()

    def __gt__(self, other) -> bool:
        """
        Allows "greater than" comparison between two cards, by rank only.
        """
        if not isinstance(other, Card):
            return NotImplemented
        return self.get_rank_value() > other.get_rank_value()

    def __le__(self, other) -> bool:
        """
        Allows "less than or equal to" comparison between two cards, by rank only.
        """
        if not isinstance(other, Card):
            return NotImplemented
        return self.get_rank_value() <= other.get_rank_value()

    def __ge__(self, other) -> bool:
        """
        Allows "greater than or equal to" comparison between two cards, by rank only.
        """
        if not isinstance(other, Card):
            return NotImplemented
        return self.get_rank_value() >= other.get_rank_value()
