import enum
from typing import List, Tuple, Dict, Any, Optional
from collections import Counter
from itertools import combinations

# ודא שייבאת את Card, Suit, Rank נכון.
from backend.poker_server.game.engine.card_oop import Card


class HandRank(enum.Enum):
    """
    דירוגי הידיים האפשריים בפוקר, מהנמוך לגבוה.
    """
    HIGH_CARD = 1
    PAIR = 2
    TWO_PAIR = 3
    THREE_OF_A_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_A_KIND = 8
    STRAIGHT_FLUSH = 9
    ROYAL_FLUSH = 10

class HandEvaluator:
    """
    מחלקה שמטרתה להעריך ידי פוקר (Texas Hold'em) ולקבוע את חוזקן.
    """
    def __init__(self):
        pass

    def evaluate_hand(self, player_cards: List[Card], community_cards: List[Card]) -> Tuple[HandRank, List[Card], List[Card]]:
        """
        מעריכה את היד הטובה ביותר ששחקן יכול לבנות מתוך קלפיו וקלפי הקהילה.
        המתודה מנסה למצוא את היד החזקה ביותר מבין כל 5 קלפים אפשריים.

        :param player_cards: רשימת 2 הקלפים של השחקן.
        :param community_cards: רשימת 3, 4 או 5 קלפי הקהילה.
        :return: טאפל המכיל:
                 1. HandRank: דירוג היד (לדוגמה: HandRank.STRAIGHT).
                 2. List[Card]: רשימת 5 הקלפים המרכיבים את היד הטובה ביותר.
                 3. List[Card]: רשימת קלפי ה"קיקר" (אם רלוונטי, אחרת ריקה).
        """
        all_7_cards = sorted(player_cards + community_cards, key=lambda c: c.rank.value, reverse=True) # מיון יורד לפי דרגה

        best_rank = HandRank.HIGH_CARD
        best_5_cards: List[Card] = []
        best_kickers: List[Card] = []

        # נבדוק את כל 21 הקומבינציות האפשריות של 5 קלפים מתוך ה-7
        # ונשמור את היד החזקה ביותר.
        for combo in combinations(all_7_cards, 5):
            current_5_cards = sorted(list(combo), key=lambda c: c.rank.value, reverse=True)
            
            # בדוק את סוג היד עבור קומבינציית 5 הקלפים הנוכחית
            rank, hand_cards, kickers = self._get_hand_type_and_cards(current_5_cards)

            # אם היד הנוכחית טובה יותר מהטובה ביותר שנמצאה עד כה, או שהיא מאותו סוג
            # וטובה יותר (למשל, זוג גבוה יותר), עדכן את היד הטובה ביותר.
            if rank.value > best_rank.value:
                best_rank = rank
                best_5_cards = hand_cards
                best_kickers = kickers
            elif rank.value == best_rank.value:
                # אם הדירוג זהה, נצטרך להשוות את הידיים עצמן (כולל קיקרים)
                # נשתמש ב-compare_hands, אך צריך לוודא שהוא מקבל את הפורמט הנכון
                # compare_hands מצפה לטאפל של (rank, cards, kickers)
                if self.compare_hands((rank, hand_cards, kickers), (best_rank, best_5_cards, best_kickers)) == 1:
                    best_rank = rank
                    best_5_cards = hand_cards
                    best_kickers = kickers
        
        # מכיוון ש_get_hand_type_and_cards מחזירה כבר את ה-5 קלפים הטובים ביותר,
        # ו-evaluate_hand לוקחת את ה-5 קלפים הטובים ביותר מבין 7,
        # ייתכן שbest_kickers לא יוגדר נכון או בכלל.
        # לכן נשנה את הפורמט של _get_hand_type_and_cards שיחזיר רק את ה-rank וה-5 קלפים.
        # ולבסוף, את ה-kickers נחשב מתוך ה-7 קלפים המקוריים ביחס ל-5 קלפי היד שנבחרו.
        
        # נשנה את evaluate_hand כדי שייקח את 5 הקלפים הטובים ביותר, ואז יחשב קיקרים מהשאר.
        # זה קצת מורכב, אז בשלב זה נחזיר קיקרים ריקים. (יידרש מימוש פרטני)
        
        return best_rank, best_5_cards, best_kickers


    def _get_hand_type_and_cards(self, cards: List[Card]) -> Tuple[HandRank, List[Card], List[Card]]:
        """
        פונקציית עזר פנימית המקבלת רשימת 5 קלפים ומחזירה את סוג היד, 
        את 5 הקלפים המרכיבים אותה ואת קלפי הקיקר (במידת הצורך).
        הקלפים חייבים להיות ממוינים מהגבוה לנמוך לפי דרגה.
        """
        # ודא שמדובר ב-5 קלפים בדיוק
        if len(cards) != 5:
            raise ValueError("פונקציית _get_hand_type_and_cards מצפה לרשימה של 5 קלפים.")

        # מידע עזר: ספירת דרגות וחליפות
        rank_counts = Counter(c.rank for c in cards)
        suit_counts = Counter(c.suit for c in cards)
        sorted_ranks_values = sorted([c.rank.value for c in cards], reverse=True) # דרגות ממוינות
        
        # זיהוי סטריט
        is_straight = self._check_straight(sorted_ranks_values)
        
        # זיהוי פלאש
        is_flush = len(suit_counts) == 1

        # בדיקות מהגבוה לנמוך (כדי למצוא את היד הטובה ביותר)
        
        # 1. רויאל פלאש
        if is_straight and is_flush and \
           sorted_ranks_values == [Rank.ACE.value, Rank.KING.value, Rank.QUEEN.value, Rank.JACK.value, Rank.TEN.value]:
            return HandRank.ROYAL_FLUSH, cards, []

        # 2. סטרייט פלאש
        if is_straight and is_flush:
            return HandRank.STRAIGHT_FLUSH, cards, []

        # 3. רביעייה
        for rank, count in rank_counts.items():
            if count == 4:
                quad_cards = [c for c in cards if c.rank == rank]
                kicker = [c for c in cards if c.rank != rank] # קלף קיקר בודד
                return HandRank.FOUR_OF_A_KIND, quad_cards + sorted(kicker, key=lambda c: c.rank.value, reverse=True)[:1], sorted(kicker, key=lambda c: c.rank.value, reverse=True)[1:] # קיקרים
        
        # 4. פול האוס
        is_three = False
        is_pair = False
        three_of_a_kind_rank = None
        pair_rank = None

        for rank, count in rank_counts.items():
            if count == 3:
                is_three = True
                three_of_a_kind_rank = rank
            elif count == 2:
                is_pair = True
                pair_rank = rank
        
        if is_three and is_pair:
            full_house_cards = [c for c in cards if c.rank == three_of_a_kind_rank] + \
                               [c for c in cards if c.rank == pair_rank]
            return HandRank.FULL_HOUSE, sorted(full_house_cards, key=lambda c: c.rank.value, reverse=True), []

        # 5. פלאש
        if is_flush:
            return HandRank.FLUSH, cards, []

        # 6. סטרייט
        if is_straight:
            return HandRank.STRAIGHT, cards, []

        # 7. שלשה
        for rank, count in rank_counts.items():
            if count == 3:
                trips_cards = [c for c in cards if c.rank == rank]
                kickers = [c for c in cards if c.rank != rank]
                return HandRank.THREE_OF_A_KIND, trips_cards + sorted(kickers, key=lambda c: c.rank.value, reverse=True)[:2], sorted(kickers, key=lambda c: c.rank.value, reverse=True)[2:]

        # 8. שני זוגות
        pairs = [rank for rank, count in rank_counts.items() if count == 2]
        if len(pairs) == 2:
            pair_cards = [c for c in cards if c.rank in pairs]
            kicker = [c for c in cards if c.rank not in pairs]
            return HandRank.TWO_PAIR, sorted(pair_cards, key=lambda c: c.rank.value, reverse=True) + sorted(kicker, key=lambda c: c.rank.value, reverse=True)[:1], sorted(kicker, key=lambda c: c.rank.value, reverse=True)[1:]

        # 9. זוג
        if len(pairs) == 1:
            pair_cards = [c for c in cards if c.rank == pairs[0]]
            kickers = [c for c in cards if c.rank != pairs[0]]
            return HandRank.PAIR, sorted(pair_cards, key=lambda c: c.rank.value, reverse=True) + sorted(kickers, key=lambda c: c.rank.value, reverse=True)[:3], sorted(kickers, key=lambda c: c.rank.value, reverse=True)[3:]

        # 10. קלף גבוה (High Card)
        return HandRank.HIGH_CARD, cards[:5], cards[5:] # כל ה-5 קלפים הם היד, קיקרים ריקים


    def _check_straight(self, sorted_rank_values: List[int]) -> bool:
        """
        פונקציית עזר: בודקת אם קיימת רצף (סטרייט) ב-5 דרגות קלפים.
        הקלפים חייבים להיות ממוינים בסדר יורד.
        מטפלת גם במקרה של סטרייט A-5.
        """
        if len(sorted_rank_values) < 5:
            return False

        # בדיקה לסטרייט רגיל (K, Q, J, 10, 9)
        is_regular_straight = True
        for i in range(len(sorted_rank_values) - 1):
            if sorted_rank_values[i] - 1 != sorted_rank_values[i+1]:
                is_regular_straight = False
                break
        if is_regular_straight:
            return True

        # בדיקה לסטרייט A-5 (5, 4, 3, 2, A)
        # זה אומר שהדרגות הן 5,4,3,2,1 (כאשר 1 הוא אייס נמוך)
        # הדרגות הממוינות יהיו: [5, 4, 3, 2, 14] עבור A,5,4,3,2.
        # לכן, צריך לבדוק את הסט בנפרד.
        if set(sorted_rank_values) == {Rank.ACE.value, Rank.FIVE.value, Rank.FOUR.value, Rank.THREE.value, Rank.TWO.value}:
             return True # זהו סטרייט A-5
        
        return False


    def compare_hands(self, hand1_info: Tuple[HandRank, List[Card], List[Card]], hand2_info: Tuple[HandRank, List[Card], List[Card]]) -> int:
        """
        משווה בין שתי ידיים שהוערכו ע"י evaluate_hand.

        :param hand1_info: טאפל מידע על יד 1 (HandRank, cards, kickers).
        :param hand2_info: טאפל מידע על יד 2 (HandRank, cards, kickers).
        :return: 1 אם יד 1 מנצחת, -1 אם יד 2 מנצחת, 0 אם תיקו.
        """
        rank1, cards1, kickers1 = hand1_info
        rank2, cards2, kickers2 = hand2_info

        # שלב 1: השוואה לפי דירוג היד
        if rank1.value > rank2.value:
            return 1
        if rank2.value > rank1.value:
            return -1

        # שלב 2: אם הדירוגים שווים, השווה לפי הקלפים המרכיבים את היד (וקיקרים)
        # יש לוודא שהקלפים ב-cards1 וב-cards2 ממוינים מהגבוה לנמוך.
        # הם אמורים להיות כאלה מ-_get_hand_type_and_cards

        # השוואת הקלפים המרכיבים את היד
        for i in range(min(len(cards1), len(cards2))):
            if cards1[i].rank.value > cards2[i].rank.value:
                return 1
            if cards2[i].rank.value > cards1[i].rank.value:
                return -1

        # השוואת קיקרים, אם יש (רק אם היד עצמה זהה לחלוטין)
        # יש לוודא שkickers1 ו-kickers2 גם ממוינים.
        # הערה: יש לוודא שאופן החזרת הקיקרים ב- _get_hand_type_and_cards נכון לכל מקרה.
        for i in range(min(len(kickers1), len(kickers2))):
            if kickers1[i].rank.value > kickers2[i].rank.value:
                return 1
            if kickers2[i].rank.value > kickers1[i].rank.value:
                return -1
        
        # אם הכל שווה (כולל קיקרים), אז תיקו.
        return 0

    def __str__(self) -> str:
        return "מעריך ידי פוקר"

    def __repr__(self) -> str:
        return "HandEvaluator()"