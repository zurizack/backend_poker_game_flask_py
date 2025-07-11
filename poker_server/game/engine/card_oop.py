from typing import Dict


class Card:
    """
    מחלקה שמייצגת קלף בודד בחפיסת קלפים.
    הייצוג הפנימי הוא קומפקטי (תו אחד לדרגה ותו אחד לצורה),
    אך ניתן להציגו באופן קריא למשתמש.
    """

    # ייצוגים קצרים ומוכרים לדרגות ולצורות
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    SUITS = ['C', 'D', 'H', 'S']

    # מילונים למיפוי הייצוגים הקצרים לשמות קריאים ולסמלים (לצורך תצוגה)
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
        קונסטרוקטור למחלקת Card.

        :param rank: דרגת הקלף (תו בודד מתוך RANKS).
        :param suit: צורת הקלף (תו בודד מתוך SUITS).
        :raises ValueError: אם הדרגה או הצורה אינן חוקיות.
        """
        if rank not in Card.RANKS:
            raise ValueError(f"דרגת קלף לא חוקית. הדרגות החוקיות הן: {', '.join(Card.RANKS)}")
        if suit not in Card.SUITS:
            raise ValueError(f"צורת קלף לא חוקית. הצורות החוקיות הן: {', '.join(Card.SUITS)}")

        self._rank = rank
        self._suit = suit

    def get_rank(self) -> str:
        """
        מחזירה את דרגת הקלף בייצוג הקצר.
        """
        return self._rank

    def get_suit(self) -> str:
        """
        מחזירה את צורת הקלף בייצוג הקצר.
        """
        return self._suit

    def get_rank_value(self) -> int:
        """
        מחזירה את הערך המספרי של דרגת הקלף.
        משמש להשוואות לוגיות (לדוגמה: 2 < 3, K > Q).
        """
        return Card.RANKS.index(self._rank) # Index in RANKS list gives numerical value
    
    def to_dict(self) -> Dict[str, str]:
        """
        ממירה את הקלף למילון הניתן לשידור דרך Socket.IO.
        """
        return {
            "rank": self._rank,
            "suit": self._suit
        }

    def __str__(self) -> str:
        """
        מחזירה ייצוג קריא של הקלף (לדוגמה: "Ace of Spades").
        """
        rank_display = Card._FULL_RANK_NAMES.get(self._rank, self._rank)
        full_suit_name = Card._FULL_SUIT_NAMES.get(self._suit, self._suit)
        suit_symbol = Card._SUIT_SYMBOLS.get(self._suit, self._suit)

        # נבחר פורמט המשלב את השם המלא עם סמל, לדוגמה: "Ace of Spades (♠)"
        return f"{rank_display} of {full_suit_name} ({suit_symbol})"

    def __repr__(self) -> str:
        """
        מחזירה ייצוג חד-משמעי של האובייקט, המשמש לדיבוג.
        """
        return f"Card(rank='{self._rank}', suit='{self._suit}')"

    def __eq__(self, other) -> bool:
        """
        מאפשרת השוואת שוויון בין שני אובייקטי Card.
        שני קלפים נחשבים שווים אם יש להם אותה דרגה ואותה צורה.
        """
        if not isinstance(other, Card):
            return NotImplemented
        return self._rank == other._rank and self._suit == other._suit

    def __lt__(self, other) -> bool:
        """
        מאפשרת השוואת "קטן מ-" בין שני קלפים, לפי דרגה בלבד.
        """
        if not isinstance(other, Card):
            return NotImplemented
        return self.get_rank_value() < other.get_rank_value()

    def __gt__(self, other) -> bool:
        """
        מאפשרת השוואת "גדול מ-" בין שני קלפים, לפי דרגה בלבד.
        """
        if not isinstance(other, Card):
            return NotImplemented
        return self.get_rank_value() > other.get_rank_value()

    def __le__(self, other) -> bool:
        """
        מאפשרת השוואת "קטן או שווה ל-" בין שני קלפים, לפי דרגה בלבד.
        """
        if not isinstance(other, Card):
            return NotImplemented
        return self.get_rank_value() <= other.get_rank_value()

    def __ge__(self, other) -> bool:
        """
        מאפשרת השוואת "גדול או שווה ל-" בין שני קלפים, לפי דרגה בלבד.
        """
        if not isinstance(other, Card):
            return NotImplemented
        return self.get_rank_value() >= other.get_rank_value()