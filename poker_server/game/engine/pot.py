from typing import List, Dict, Tuple, Optional, Any
from backend.poker_server.game.engine.player_oop import Player 
from backend.poker_server.game.engine.chip_stack import Chips 


class Pot:
    """
    מחלקה שמנהלת את הקופות (Pot) על השולחן.
    אחראית על צבירת הימורים, יצירת קופות צדדיות (Side Pots)
    במקרה של אול-אין, וחלוקת הקופות לשחקנים הזוכים.
    ניהול הכספים בקופות מבוצע כעת באמצעות אובייקטי Chips ייעודיים.
    """
    def __init__(self):
        """
        קונסטרוקטור למחלקת Pot.
        מאפס את הקופה הראשית ואת רשימת הקופות הצדדיות.
        """
        self._main_pot_chips: Chips = Chips(0) 
        # כל קופה צדדית תהיה מילון:
        # {
        #   'amount_chips': Chips,          # אובייקט Chips עבור סכום הכסף בקופה הצדדית
        #   'eligible_players_ids': List[str], # רשימת ה-player_id של השחקנים הזכאים לזכות בקופה זו
        #   'all_in_bet_level': int         # סכום ההימור המקסימלי שהוצב לקופה זו
        # }
        self._side_pots: List[Dict] = []

    def _create_new_side_pot(self, all_in_bet_level: int, eligible_players: List[Player]):
        """
        פונקציית עזר פנימית ליצירת קופה צדדית חדשה.
        :param all_in_bet_level: רמת ההימור שהובילה ליצירת קופה זו (ההימור ששחקן אול-אין שם).
        :param eligible_players: רשימת השחקנים הזכאים לזכות בקופה זו.
        """
        eligible_ids = [player.user_id for player in eligible_players if isinstance(player, Player)] # שימוש ב-player.user_id
        self._side_pots.append({
            'amount_chips': Chips(0), 
            'eligible_players_ids': eligible_ids,
            'all_in_bet_level': all_in_bet_level
        })

    def add_bet(self, player: Player, bet_amount: int, current_round_max_bet: int):
        """
        מוסיף הימור של שחקן לקופות.
        מתודה זו מטפלת בלוגיקת הקופות הראשיות והצדדיות במצבי אול-אין.

        :param player: אובייקט השחקן שמבצע את ההימור.
        :param bet_amount: סכום ההימור הכולל ששחקן שם עד כה ביד זו.
        :param current_round_max_bet: ההימור הגבוה ביותר ששולם ע"י שחקן יריב בסבב הימורים זה.
        """
        # זו מתודה מורכבת שתידרש לוגיקה עדינה מאוד עבור Side Pots.
        # בשלב זה, נשאיר את הלוגיקה המורכבת של Side Pots בתוך TODOs
        # ונתמקד במבנה הבסיסי.
        
        # לוגיקה פשוטה וראשונית:
        # כל הימור חדש שמתקבל נכנס לקופה הראשית, אם אין קופות צדדיות.
        # אם יש קופות צדדיות, צריך לנתב את הכסף נכון.
        
        # נניח ש-`bet_amount` הוא הסכום שהשחקן שם *בסבב הימורים זה*.
        self._main_pot_chips.add(bet_amount) 

        # TODO: Implement full Side Pot contribution logic here.
        # This will involve iterating through existing side pots and allocating
        # `bet_amount` based on `all_in_bet_level` and player eligibility.
        # If `bet_amount` exceeds existing pot levels, new side pots might be needed.

    def collect_round_bets(self, current_player_bets: Dict[int, int], all_players_total_bets_in_hand: Dict[int, int]): # שינוי מ-str ל-int עבור player_id
        """
        אוספת את ההימורים מסיבוב ההימורים הנוכחי ומחלקת אותם לקופות המתאימות,
        תוך כדי ניהול קופות צדדיות.

        :param current_player_bets: מילון של {player_id: amount_bet_in_this_round}
                                   הסכום שכל שחקן הימר *בסיבוב הנוכחי*.
        :param all_players_total_bets_in_hand: מילון של {player_id: total_amount_bet_in_hand_so_far}
                                               הסכום הכולל שכל שחקן הימר *ביד זו* (מצטבר).
        """
        total_round_contribution = sum(current_player_bets.values())

        self._main_pot_chips.add(total_round_contribution)

        # TODO: Implement complex Side Pot creation and allocation logic based on
        # `all_players_total_bets_in_hand` and `current_player_bets`.
        # This is where the core logic for capping bets and creating new side pots
        # (using `_create_new_side_pot`) will reside.
        # It will likely involve iterating through players by their total bet amount
        # and distributing their contributions across main and side pots.

    def distribute_pot(self, winning_hands: List[Tuple[Player, int, str]]):
        """
        מחלקת את הקופות לשחקנים הזוכים.
        המחלקה צריכה לטפל גם במקרה של חלוקת קופה בין מספר זוכים.

        :param winning_hands: רשימה של טאפלים, כאשר כל טאפל מכיל:
                              (אובייקט Player זוכה, סכום זכייה מתוך הקופה הכוללת, סיבת הזכייה/תיאור)
                              **הערה:** ה-amount_to_win יהיה מחושב מראש מחוץ למחלקה זו.
        """
        if not winning_hands:
            print("אין זוכים לחלק קופה.")
            return

        # TODO: Implement complex Side Pot distribution logic here.
        # This will involve iterating through side pots (likely sorted by all_in_bet_level)
        # and distributing their `amount_chips` to eligible winners first,
        # before distributing the main pot.

        # בינתיים, חלוקת הקופה הראשית:
        total_main_pot_amount = self._main_pot_chips.get_amount()
        total_winnings_requested = sum(amount for _, amount, _ in winning_hands)

        if total_winnings_requested > total_main_pot_amount:
            print(f"אזהרה: סכום הזכייה המבוקש ({total_winnings_requested}) גדול מהקופה הראשית ({total_main_pot_amount}).")
            # במצב אמיתי, צריך לטפל בזה בצורה חכמה יותר (לדוגמה, לחלק באופן פרופורציונלי).

        for player, amount, reason in winning_hands:
            if player: 
                try:
                    self._main_pot_chips.remove(amount) 
                    player.add_chips_to_table(amount)    
                    print(f"שחקן {player.username} (ID: {player.user_id}) זכה ב-{amount} צ'יפים. סיבה: {reason}")
                except ValueError as e:
                    print(f"שגיאה בחלוקת צ'יפים לשחקן {player.username}: {e}")

        self._main_pot_chips = Chips(0) 

    def reset_pots(self):
        """
        מאפס את כל הקופות לקראת יד חדשה.
        """
        self._main_pot_chips = Chips(0) 
        self._side_pots = []

    def get_total_pot_size(self) -> int:
        """
        מחזירה את הגודל הכולל של כל הקופות (ראשיות וצדדיות).
        """
        total_size = self._main_pot_chips.get_amount() 
        for pot_data in self._side_pots:
            total_size += pot_data['amount_chips'].get_amount() 
        return total_size

    def __str__(self) -> str:
        """
        מחזירה ייצוג קריא של מצב הקופות.
        """
        s = f"קופה ראשית: {self._main_pot_chips.get_amount()} צ'יפים" 
        if self._side_pots:
            s += "\n    קופות צדדיות:"
            for i, sp in enumerate(self._side_pots):
                eligible_names = ", ".join(str(id) for id in sp['eligible_players_ids']) # ודא ש-ID הוא string עבור join
                s += (f"\n      {i+1}. סכום: {sp['amount_chips'].get_amount()} (רמת הימור: {sp['all_in_bet_level']}) " 
                      f"- זכאים: [{eligible_names}]")
        return s

    def __repr__(self) -> str:
        """
        מחזירה ייצוג חד-משמעי של האובייקט, המשמש לדיבוג.
        """
        return (
            f"Pot(main_pot_chips={repr(self._main_pot_chips)}, side_pots={self._side_pots})" 
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        ממירה את אובייקט ה-Pot למילון המתאים לסריאליזציית JSON.
        """
        side_pots_data = []
        for sp in self._side_pots:
            side_pots_data.append({
                'amount': sp['amount_chips'].get_amount(), # קבל את הערך המספרי של הצ'יפים
                'eligible_players_ids': sp['eligible_players_ids'],
                'all_in_bet_level': sp['all_in_bet_level']
            })

        return {
            'main_pot_amount': self._main_pot_chips.get_amount(), # קבל את הערך המספרי
            'total_pot_amount': self.get_total_pot_size(), # קבל את הערך המספרי הכולל
            'side_pots': side_pots_data
        }

