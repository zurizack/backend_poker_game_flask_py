# backend/poker_server/game/engine/chip_stack.py

import logging

logger = logging.getLogger(__name__)

class Chips:
    """
    A class representing a player's chip stack.
    Manages adding, removing, and checking balance.
    """
    def __init__(self, initial_amount: float = 0.0):
        """
        Constructor for the Chips class.
        :param initial_amount: The initial amount of chips.
        """
        if not isinstance(initial_amount, (int, float)) or initial_amount < 0:
            raise ValueError("Initial chip amount must be a non-negative number.")
        self._amount: float = float(initial_amount)
        logger.debug(f"Chips stack initialized with {self._amount} chips.")

    def add(self, amount: float):
        """
        Adds chips to the stack.
        :param amount: The amount of chips to add.
        :raises ValueError: If the amount is not a positive number.
        """
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("The amount to add must be a positive number.")
        self._amount += float(amount)
        logger.debug(f"Added {amount} chips. Current total: {self._amount}.")

    def remove(self, amount: float):
        """
        Removes chips from the stack.
        :param amount: The amount of chips to remove.
        :raises ValueError: If the amount is not a positive number, or if there are not enough chips.
        """
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("The amount to remove must be a positive number.")
        if self._amount < amount:
            raise ValueError(f"Not enough chips. Current: {self._amount}, trying to remove: {amount}.")
        self._amount -= float(amount)
        logger.debug(f"Removed {amount} chips. Current total: {self._amount}.")

    def get_amount(self) -> float:
        """
        Returns the current amount of chips in the stack.
        """
        return self._amount

    def can_afford(self, amount: float) -> bool:
        """
        Checks if there are enough chips in the stack to cover a certain amount.
        :param amount: The amount to check.
        :return: True if there are enough, False otherwise.
        """
        if not isinstance(amount, (int, float)) or amount < 0:
            return False # Negative or invalid amount
        return self._amount >= amount

    def __str__(self) -> str:
        """
        String representation of the chip stack.
        """
        return f"{self._amount} chips"

    def __repr__(self) -> str:
        """
        Official representation of the object, for debugging.
        """
        return f"Chips(initial_amount={self._amount})"
