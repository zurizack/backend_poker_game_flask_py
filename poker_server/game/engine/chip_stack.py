# backend/poker_server/game/engine/chip_stack.py

import logging

logger = logging.getLogger(__name__)

class Chips:
    """
    מחלקה המייצגת ערימת צ'יפים של שחקן.
    מנהלת את הוספה, הסרה ובדיקת יתרה.
    """
    def __init__(self, initial_amount: float = 0.0): # ✅ שינוי ל-float
        """
        קונסטרוקטור למחלקת Chips.
        :param initial_amount: כמות הצ'יפים ההתחלתית.
        """
        if not isinstance(initial_amount, (int, float)) or initial_amount < 0:
            raise ValueError("Initial chip amount must be a non-negative number.")
        self._amount: float = float(initial_amount) # ✅ ודא שזה float
        logger.debug(f"Chips stack initialized with {self._amount} chips.")

    def add(self, amount: float): # ✅ שינוי ל-float
        """
        מוסיף צ'יפים לערימה.
        :param amount: כמות הצ'יפים להוספה.
        :raises ValueError: אם הסכום אינו מספר חיובי.
        """
        if not isinstance(amount, (int, float)) or amount <= 0: # ✅ תמיכה ב-float
            raise ValueError("The amount to add must be a positive number.")
        self._amount += float(amount) # ✅ ודא שזה float
        logger.debug(f"Added {amount} chips. Current total: {self._amount}.")

    def remove(self, amount: float): # ✅ שינוי ל-float
        """
        מסיר צ'יפים מהערימה.
        :param amount: כמות הצ'יפים להסרה.
        :raises ValueError: אם הסכום אינו מספר חיובי, או אם אין מספיק צ'יפים.
        """
        if not isinstance(amount, (int, float)) or amount <= 0: # ✅ תמיכה ב-float
            raise ValueError("The amount to remove must be a positive number.")
        if self._amount < amount:
            raise ValueError(f"Not enough chips. Current: {self._amount}, trying to remove: {amount}.")
        self._amount -= float(amount) # ✅ ודא שזה float
        logger.debug(f"Removed {amount} chips. Current total: {self._amount}.")

    def get_amount(self) -> float: # ✅ שינוי ל-float
        """
        מחזירה את כמות הצ'יפים הנוכחית בערימה.
        """
        return self._amount

    def can_afford(self, amount: float) -> bool: # ✅ שינוי ל-float
        """
        בודק אם יש מספיק צ'יפים בערימה כדי לכסות סכום מסוים.
        :param amount: הסכום לבדיקה.
        :return: True אם יש מספיק, False אחרת.
        """
        if not isinstance(amount, (int, float)) or amount < 0: # ✅ תמיכה ב-float
            return False # סכום שלילי או לא חוקי
        return self._amount >= amount

    def __str__(self) -> str:
        """
        ייצוג מחרוזתי של ערימת הצ'יפים.
        """
        return f"{self._amount} chips"

    def __repr__(self) -> str:
        """
        ייצוג רשמי של האובייקט, לדיבוג.
        """
        return f"Chips(initial_amount={self._amount})"

