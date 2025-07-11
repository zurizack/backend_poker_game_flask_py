import enum
from typing import List, Optional

from backend.poker_server.game.engine.card_oop import Card # ודא שזה הייבוא הנכון של מחלקת Card

# הגדרת Enum למצבי היד של השחקן
class PlayerHandStatus(enum.Enum):
    """
    מייצג את מצבי השחקן השונים ביד פוקר נוכחית.
    """
    ACTIVE = "ACTIVE"                       # פעיל, יכול לבצע פעולות
    FOLDED = "FOLDED"                       # קיפל את היד, לא משתתף בקופה
    ALL_IN = "ALL_IN"                       # הימר את כל הצ'יפים, עדיין משתתף בקופה
    # שחקן חדש שהתיישב או שחקן ותיק שחוזר, ממתין ליד הבאה.
    WAITING_FOR_NEW_HAND = "WAITING_FOR_NEW_HAND" 
    # שחקן שיושב ליד השולחן אך אינו משתתף ביד הנוכחית (לדוגמה, לקח הפסקה קצרה).
    SITTING_OUT = "SITTING_OUT"
    NOT_SEATED = "NOT_SEATED"

# הגדרת Enum לפעולות השחקן (ייתכן שקיים כבר במקום אחר, אך נכלל כאן לשלמות)
class PlayerAction(enum.Enum):
    """
    מייצג את הפעולות האפשריות ששחקן יכול לבצע.
    """
    CHECK = "CHECK"
    CALL = "CALL"
    RAISE = "RAISE"
    BET = "BET"
    FOLD = "FOLD"
    ALL_IN = "ALL_IN" # יכול להיות פעולה בפני עצמה, או כחלק מ-BET/RAISE/CALL


class PlayerHand:
    """
    מחלקה שמייצגת את מצב היד הספציפית של שחקן בתוך יד פוקר מתנהלת.
    מכילה את הקלפים, סטטוס היד, ההימור ביד הנוכחית ופעולה אחרונה.
    """
    def __init__(self):
        """
        קונסטרוקטור למחלקת PlayerHand.
        מאפס את כל הנתונים של היד, מוגדר כ-WAITING_FOR_NEW_HAND כברירת מחדל.
        """
        self._cards: List[Card] = []
        self._status: PlayerHandStatus = PlayerHandStatus.WAITING_FOR_NEW_HAND
        self._current_bet_in_hand: int = 0  # סך הצ'יפים שהשחקן הימר ביד זו (על פני כל הסיבובים).
        self._last_action: Optional[PlayerAction] = None

    def set_cards(self, cards: List[Card]):
        """
        מגדיר את קלפי היד הסמויים של השחקן.
        :param cards: רשימה של שני אובייקטי Card.
        :raises ValueError: אם הרשימה אינה מכילה בדיוק 2 קלפים.
        """
        if len(cards) != 2:
            raise ValueError("יד פוקר חייבת להכיל בדיוק 2 קלפים.")
        self._cards = list(cards) # שומר עותק

    def clear_cards(self):
        """
        מנקה את קלפי היד של השחקן (לקראת יד חדשה).
        """
        self._cards = []

    def get_cards(self) -> List[Card]:
        """
        מחזירה עותק של קלפי היד הסמויים של השחקן.
        """
        return list(self._cards) # מחזיר עותק כדי למנוע שינוי ישיר מבחוץ

    def set_status(self, status: PlayerHandStatus):
        """
        מגדירה את מצב היד הנוכחי של השחקן.
        :param status: אחד מערכי PlayerHandStatus.
        """
        self._status = status

    def get_status(self) -> PlayerHandStatus:
        """
        מחזירה את מצב היד הנוכחי של השחקן.
        """
        return self._status

    def add_to_bet(self, amount: int):
        """
        מוסיף סכום להימור המצטבר של השחקן ביד זו.
        :param amount: הסכום להוספה. חייב להיות חיובי.
        :raises ValueError: אם הסכום שלילי.
        """
        if amount < 0:
            raise ValueError("סכום ההימור חייב להיות חיובי.")
        self._current_bet_in_hand += amount

    def get_bet_in_hand(self) -> int:
        """
        מחזירה את סך הצ'יפים שהשחקן הימר ביד זו (על פני כל הסיבובים).
        """
        return self._current_bet_in_hand

    def reset_bet(self):
        """
        מאפס את סכום ההימור המצטבר ביד (לקראת יד חדשה).
        """
        self._current_bet_in_hand = 0

    def set_last_action(self, action: PlayerAction):
        """
        מגדירה את הפעולה האחרונה שהשחקן ביצע.
        :param action: אחד מערכי PlayerAction.
        """
        self._last_action = action

    def get_last_action(self) -> Optional[PlayerAction]:
        """
        מחזירה את הפעולה האחרונה שהשחקן ביצע.
        """
        return self._last_action

    def reset_state(self):
        """
        מאפסת את כל המצבים הספציפיים ליד לקראת תחילת יד חדשה.
        מגדירה את הסטטוס ל-ACTIVE כברירת מחדל ליד חדשה.
        """
        self.clear_cards()
        self.reset_bet()
        self.set_status(PlayerHandStatus.ACTIVE) # ברירת מחדל: פעיל ביד חדשה
        self.set_last_action(None)

    def __str__(self) -> str:
        """
        מחזירה ייצוג קריא של מצב היד, למטרות תצוגה.
        """
        status_he = {
            PlayerHandStatus.ACTIVE: "פעיל",
            PlayerHandStatus.FOLDED: "קיפל",
            PlayerHandStatus.ALL_IN: "אול-אין",
            PlayerHandStatus.WAITING_FOR_NEW_HAND: "ממתין ליד חדשה",
            PlayerHandStatus.SITTING_OUT: "יושב בחוץ"
        }
        status_display = status_he.get(self.get_status(), "לא ידוע")
        
        cards_display = ", ".join(str(card) for card in self._cards) if self._cards else "אין קלפים"
        last_action_display = self.get_last_action().value if self.get_last_action() else "אין"

        return (
            f"מצב יד: {status_display} "
            f"- קלפים: [{cards_display}] "
            f"- הימור ביד: {self._current_bet_in_hand} "
            f"- פעולה אחרונה: {last_action_display}"
        )

    def __repr__(self) -> str:
        """
        מחזירה ייצוג חד-משמעי של האובייקט, המשמש לדיבוג ופיתוח.
        """
        cards_repr = [repr(card) for card in self._cards]
        return (
            f"PlayerHand(cards={cards_repr}, status={self._status.value}, "
            f"current_bet_in_hand={self._current_bet_in_hand}, "
            f"last_action={self._last_action.value if self._last_action else 'None'})"
        )