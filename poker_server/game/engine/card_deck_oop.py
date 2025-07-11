import random
from typing import List, Optional
from backend.poker_server.game.engine.card_oop import Card

class CardDeck:
    """
    מחלקה שמייצגת חבילת קלפים סטנדרטית (52 קלפים) ומנהלת את פעולות הערבוב והחלוקה.
    היא תומכת גם ביצירת חבילה חדשה וגם בשחזור מצב חבילה קיים.
    """

    def __init__(self, initial_cards: Optional[List[Card]] = None):
        """
        קונסטרוקטור למחלקת CardDeck.

        :param initial_cards: (אופציונלי) רשימה של אובייקטי Card.
                              אם מסופק, החבילה תאותחל עם הקלפים הללו בסדר הנתון.
                              אם None (ברירת מחדל), החבילה תאותחל כחבילה חדשה של 52 קלפים מעורבבים.
        """
        if initial_cards is None:
            # אם לא סופקו קלפים ראשוניים, בנה חבילה חדשה וערבב אותה
            self._cards: List[Card] = []
            self._initialize_deck()
            self.shuffle()
        else:
            # אם סופקו קלפים ראשוניים (לצורך שחזור), השתמש בהם
            # חשוב ליצור עותק כדי לא לשנות את הרשימה המקורית אם היא מגיעה מבחוץ
            self._cards = list(initial_cards) 

    def _initialize_deck(self):
        """
        פונקציית עזר פרטית ליצירת 52 קלפים סטנדרטיים ומסודרים.
        """
        self._cards = [] # וודא שהרשימה ריקה לפני בנייה מחדש
        for suit in Card.SUITS:
            for rank in Card.RANKS:
                self._cards.append(Card(rank, suit))

    def shuffle(self):
        """
        מערבב את הקלפים בחבילה באופן רנדומלי.
        """
        random.shuffle(self._cards)

    def deal_card(self) -> Card:
        """
        שולף ומחזיר קלף אחד מראש החבילה.
        (הקלף האחרון ברשימה נחשב "ראש" החבילה בפייתון לנוחות ה-pop).

        :return: אובייקט Card.
        :raises IndexError: אם החבילה ריקה.
        """
        if not self._cards:
            raise IndexError("אין קלפים נותרים בחבילה.")
        return self._cards.pop()

    def num_cards_left(self) -> int:
        """
        מחזירה את מספר הקלפים שנותרו בחבילה.
        """
        return len(self._cards)

    def reset(self):
        """
        מאפס את החבילה למצב ההתחלתי שלה: 52 קלפים חדשים ומעורבבים.
        """
        self._initialize_deck()
        self.shuffle()

    def get_cards(self) -> List[Card]:
        """
        מחזירה עותק של רשימת הקלפים הנוכחית בחבילה.
        שימושית לשמירת מצב החבילה ושחזורה.

        :return: רשימה של אובייקטי Card.
        """
        return list(self._cards) # מחזיר עותק כדי למנוע שינוי ישיר מבחוץ

    def __len__(self) -> int:
        """
        מאפשר להשתמש בפונקציה המובנית len() על אובייקט CardDeck.
        לדוגמה: len(my_deck).
        """
        return self.num_cards_left()

    def __str__(self) -> str:
        """
        מחזירה ייצוג קריא של מצב החבילה.
        """
        return f"חבילת קלפים עם {len(self)} קלפים שנותרו."

    def __repr__(self) -> str:
        """
        מחזירה ייצוג חד-משמעי של האובייקט, המשמש לדיבוג.
        מציגה את מספר הקלפים ואת חמשת הקלפים העליונים (האחרונים ברשימה).
        """
        # לצורך דיבוג, נציג גם את הקלפים שנותרו בחבילה.
        # אזהרה: עבור חבילה מלאה, זה יכול להיות פלט ארוך.
        return f"CardDeck(cards_left={len(self)}, top_cards={[repr(card) for card in self._cards[-5:]]})"