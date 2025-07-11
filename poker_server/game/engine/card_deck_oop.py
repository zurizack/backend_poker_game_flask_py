import random
from typing import List, Optional
from backend.poker_server.game.engine.card_oop import Card

class CardDeck:
    """
    A class that represents a standard deck of cards (52 cards) and manages shuffling and dealing operations.
    It supports both creating a new deck and restoring an existing deck state.
    """

    def __init__(self, initial_cards: Optional[List[Card]] = None):
        """
        Constructor for the CardDeck class.

        :param initial_cards: (Optional) A list of Card objects.
                                If provided, the deck will be initialized with these cards in the given order.
                                If None (default), the deck will be initialized as a new shuffled 52-card deck.
        """
        if initial_cards is None:
            # If no initial cards are provided, build a new deck and shuffle it
            self._cards: List[Card] = []
            self._initialize_deck()
            self.shuffle()
        else:
            # If initial cards are provided (for restoration), use them
            # It's important to create a copy to avoid modifying the original list if it comes from outside
            self._cards = list(initial_cards) 

    def _initialize_deck(self):
        """
        Private helper function to create 52 standard, ordered cards.
        """
        self._cards = [] # Ensure the list is empty before rebuilding
        for suit in Card.SUITS:
            for rank in Card.RANKS:
                self._cards.append(Card(rank, suit))

    def shuffle(self):
        """
        Shuffles the cards in the deck randomly.
        """
        random.shuffle(self._cards)

    def deal_card(self) -> Card:
        """
        Draws and returns one card from the top of the deck.
        (The last card in the list is considered the "top" of the deck in Python for pop convenience).

        :return: A Card object.
        :raises IndexError: If the deck is empty.
        """
        if not self._cards:
            raise IndexError("No cards left in the deck.")
        return self._cards.pop()

    def num_cards_left(self) -> int:
        """
        Returns the number of cards remaining in the deck.
        """
        return len(self._cards)

    def reset(self):
        """
        Resets the deck to its initial state: 52 new and shuffled cards.
        """
        self._initialize_deck()
        self.shuffle()

    def get_cards(self) -> List[Card]:
        """
        Returns a copy of the current list of cards in the deck.
        Useful for saving and restoring the deck's state.

        :return: A list of Card objects.
        """
        return list(self._cards) # Returns a copy to prevent direct modification from outside

    def __len__(self) -> int:
        """
        Allows using the built-in len() function on a CardDeck object.
        For example: len(my_deck).
        """
        return self.num_cards_left()

    def __str__(self) -> str:
        """
        Returns a readable representation of the deck's state.
        """
        return f"Card deck with {len(self)} cards remaining."

    def __repr__(self) -> str:
        """
        Returns an unambiguous representation of the object, used for debugging.
        Shows the number of cards and the top five cards (the last ones in the list).
        """
        # For debugging purposes, we will also show the cards remaining in the deck.
        # Warning: For a full deck, this can be a long output.
        return f"CardDeck(cards_left={len(self)}, top_cards={[repr(card) for card in self._cards[-5:]]})"
