# backend/poker_server/game/engine/table_oop.py

import logging
from typing import Dict, Any, List, Optional
# ודא שהייבואים האלה קיימים:
from backend.poker_server.game.engine.player_oop import Player # ודא שזהו קובץ ה-Player המעודכן
from backend.poker_server.game.engine.card_oop import Card 
from backend.poker_server.game.engine.hand_evaluator_oop import HandEvaluator 
from backend.poker_server.game.engine.pot import Pot # ✅ תיקון: שינוי ל-pot_oop
from backend.poker_server.game.engine.betting_round import BettingRound, BettingRoundStatus 
from backend.poker_server.game.engine.card_deck_oop import CardDeck # ✅ תיקון: שינוי ל-deck_oop
from backend.poker_server.game.engine.player_hand import PlayerHandStatus, PlayerAction 
import enum 

logger = logging.getLogger(__name__)

class TableStatus(enum.Enum):
    """
    סטטוסים אפשריים לשולחן.
    """
    WAITING_FOR_PLAYERS = "waiting_for_players"
    READY_TO_START = "ready_to_start"
    IN_PROGRESS = "in_progress"
    GAME_OVER = "game_over" # לדוגמה, פחות מ-2 שחקנים עם צ'יפים


class Table:
    """
    מחלקה המייצגת שולחן פוקר בודד (Texas Hold'em).
    מנהלת את כל הלוגיקה של המשחק על השולחן.
    """
    def __init__(self, table_id: str, name: str, max_players: int, small_blind: float, big_blind: float, hand_evaluator: HandEvaluator): # שינוי small_blind, big_blind ל-float
        """
        קונסטרוקטור למחלקת Table.

        :param table_id: מזהה השולחן (כעת סטרינג).
        :param name: שם השולחן.
        :param max_players: מספר השחקנים המקסימלי שיכולים לשבת בשולחן.
        :param small_blind: גובה הסמול בליינד.
        :param big_blind: גובה הביג בליינד.
        :param hand_evaluator: אובייקט HandEvaluator לדירוג ידיים.
        """
        self._table_id: str = table_id
        self._name: str = name 
        self._max_players: int = max_players
        self._small_blind: float = small_blind
        self._big_blind: float = big_blind

        self._status: TableStatus = TableStatus.WAITING_FOR_PLAYERS

        # שחקנים בשולחן, ממופים לפי מספר כיסא
        self._seats: Dict[int, Optional[Player]] = {i: None for i in range(1, max_players + 1)} # כיסאות 1 עד max_players
        self._players: Dict[int, Player] = {} # {player_id: Player_object} - שחקנים יושבים
        
        self._viewers: Dict[int, Player] = {} # {player_id: Player_object} - צופים בלבד

        self._deck: CardDeck = CardDeck() # ✅ תיקון: שינוי ל-Deck
        self._pot: Pot = Pot()
        self._hand_evaluator: HandEvaluator = hand_evaluator # הזרקת תלות

        # מצב היד הנוכחית
        self._community_cards: List[Card] = [] # קלפי הקהילה (Flop, Turn, River)
        self._current_dealer_seat_index: int = -1 # מספר הכיסא של הדילר הנוכחי
        self._current_hand_number: int = 0 # מספר היד הנוכחי

        self._betting_round: Optional[BettingRound] = None # אובייקט סבב הימורים נוכחי

        logger.info(f"Table '{self._name}' (ID: {self._table_id}) initialized.") 
        print(f"שולחן '{self._name}' (ID: {self._table_id}) נוצר.") 

    # --- Properties (גישה ישירה לנתונים) ---
    @property
    def table_id(self) -> str:
        return self._table_id

    @property
    def name(self) -> str: 
        return self._name

    @property
    def max_players(self) -> int:
        return self._max_players

    @property
    def small_blind(self) -> float: # שינוי ל-float
        return self._small_blind

    @property
    def big_blind(self) -> float: # שינוי ל-float
        return self._big_blind

    @property
    def status(self) -> TableStatus:
        return self._status

    @property
    def num_seated_players(self) -> int:
        return len(self._players) # מבוסס על מספר השחקנים במילון

    @property
    def community_cards(self) -> List[Card]:
        return self._community_cards

    @property
    def pot(self) -> Pot:
        return self._pot

    @property
    def current_dealer_seat_index(self) -> int:
        return self._current_dealer_seat_index

    @property
    def current_hand_number(self) -> int:
        return self._current_hand_number

    @property
    def betting_round(self) -> Optional[BettingRound]:
        return self._betting_round

    # --- ניהול שחקנים ---
    def take_seat(self, player: Player, seat_number: int, buy_in_amount: float) -> bool:
        """
        מושיב שחקן בכיסא ספציפי בשולחן.
        :param player: אובייקט Player שרוצה לשבת.
        :param seat_number: מספר הכיסא (1 עד max_players).
        :param buy_in_amount: כמות הצ'יפים שהשחקן קונה.
        :return: True אם ההושבה הצליחה, False אחרת.
        """
        if not (1 <= seat_number <= self._max_players):
            logger.warning(f"Seat {seat_number} is out of bounds for table {self._table_id} (max {self._max_players}).")
            return False
        
        if self._seats[seat_number] is not None:
            logger.warning(f"Seat {seat_number} on table {self._table_id} is already occupied.")
            return False
        
        # ✅ בדיקה: אם השחקן כבר יושב במושב זה בשולחן זה
        if player.is_seated_at_table(self.table_id):
            logger.warning(f"Player {player.username} (ID: {player.user_id}) is already seated at table {self.table_id}. Cannot take seat again.")
            return False

        # ודא שלשחקן יש מספיק צ'יפים בחשבון הכללי ל-buy-in
        if player.get_user_total_chips() < buy_in_amount:
            logger.warning(f"Player {player.username} (ID: {player.user_id}) has insufficient chips ({player.get_user_total_chips()}) for buy-in of {buy_in_amount}.")
            return False

        # ✅ הסר את השחקן מרשימת הצופים של *שולחן זה* אם הוא היה צופה
        if player.is_viewing_table(self.table_id): # השתמש במתודה החדשה של Player
            self.remove_viewer(player.user_id) # הסר אותו מרשימת הצופים של שולחן זה
            logger.info(f"Player {player.username} (ID: {player.user_id}) removed from viewer list of table {self.table_id} before seating.")
        # בצע את ה-buy-in
        try:
            player.perform_buy_in(self.table_id, buy_in_amount) # ✅ העבר table_id
        except ValueError as e:
            logger.error(f"Error during buy-in for player {player.username}: {e}")
            return False

        # הושב את השחקן
        self._seats[seat_number] = player
        self._players[player.user_id] = player # הוסף לרשימת השחקנים הפעילים בשולחן (מפתח לפי player_id)
        player.set_seated_data_for_table(self._table_id, seat_number) # ✅ תיקון: השתמש ב-set_seated_data_for_table
        logger.info(f"Player {player.username} (ID: {player.user_id}) successfully took seat {seat_number} on table {self._table_id} with {buy_in_amount} chips.")
        print(f"שחקן {player.username} התיישב בכיסא {seat_number}.")
        
        # עדכון סטטוס השולחן אם יש מספיק שחקנים להתחלה
        if self.num_seated_players >= 2 and self.status == TableStatus.WAITING_FOR_PLAYERS:
            self._status = TableStatus.READY_TO_START
            logger.info(f"Table {self.name} is now {self.status.value}.")
            print(f"שולחן {self.name} כעת במצב: {self.status.value}")
            
        return True

    def remove_player(self, player_id: int) -> bool: 
        """
        מסיר שחקן מהשולחן על פי ה-ID שלו.
        :param player_id: ה-ID של השחקן להסרה.
        :return: True אם השחקן הוסר בהצלחה, False אחרת.
        """
        player_to_remove = self._players.get(player_id)
        if player_to_remove:
            seat_num = player_to_remove.get_seat_number(self.table_id) # ✅ השתמש ב-get_seat_number
            if seat_num is not None:
                self._seats[seat_num] = None # פנה את הכיסא
            del self._players[player_id] # הסר מהמילון הראשי
            
            # TODO: לטפל בצ'יפים שנותרו לשחקן (להחזיר לחשבון המשתמש הכללי).
            player_to_remove.leave_table_position(self.table_id) # ✅ קורא למתודה ב-Player כדי לאפס את מצבו ולהחזיר צ'יפים

            logger.info(f"שחקן {player_to_remove.username} עזב את כיסא {seat_num} בשולחן {self.table_id}.")
            print(f"שחקן {player_to_remove.username} עזב את כיסא {seat_num}.")

            if self.num_seated_players < 2 and self.status == TableStatus.IN_PROGRESS:
                self._status = TableStatus.WAITING_FOR_PLAYERS
                logger.info(f"Table {self.name} is now {self.status.value} (not enough players).")
                print(f"שולחן {self.name} כעת במצב: {self.status.value} (אין מספיק שחקנים).")
                if self.betting_round:
                    self._betting_round = None 
                    self._determine_winner_and_distribute_pot(skip_showdown=True)
            return True
        logger.warning(f"שגיאה: שחקן עם ID {player_id} לא נמצא בשולחן.")
        print(f"שגיאה: שחקן עם ID {player_id} לא נמצא בשולחן.")
        return False

    def get_player_by_id(self, player_id: int) -> Optional[Player]: 
        """מחזירה אובייקט שחקן יושב לפי ID."""
        return self._players.get(player_id)

    def get_player_by_seat(self, seat_number: int) -> Optional[Player]:
        """מחזירה אובייקט שחקן יושב לפי מספר כיסא."""
        # ✅ נצטרך לחפש לפי seat_number במילון _seats
        return self._seats.get(seat_number)

    def get_seated_players(self) -> List[Player]:
        """
        מחזירה רשימה של כל השחקנים היושבים כרגע בשולחן, ממוינים לפי מספר כיסא.
        """
        # ✅ מילון _players כעת ממופה לפי player_id, לא seat_number.
        # נצטרך למיין לפי seat_number של אובייקט Player
        # השתמש ב-self._players.values() כדי לקבל את כל אובייקטי השחקנים היושבים
        # הוספתי תנאי ל-lambda כדי למנוע שגיאות אם get_seat_number מחזיר None (למרות שאמור להיות יושב)
        return sorted([p for p in self._players.values()], key=lambda p: p.get_seat_number(self.table_id) if p.is_seated_at_table(self.table_id) else float('inf')) 
    
    def get_active_players_in_hand(self) -> List[Player]:
        """
        מחזירה רשימה של שחקנים שעדיין פעילים ביד הנוכחית (לא קיפלו ולא יושבים בחוץ, ויש להם צ'יפים).
        """
        return [p for p in self.get_seated_players() 
                if p.get_hand_status(self.table_id) not in [PlayerHandStatus.FOLDED, PlayerHandStatus.SITTING_OUT] # ✅ העבר table_id
                and p.get_chips_on_table(self.table_id) > 0] # ✅ העבר table_id
    
    # --- ניהול צופים ---
    def add_viewer(self, viewer_player: Player) -> bool:
        """
        מוסיף שחקן לרשימת הצופים של השולחן.
        :param viewer_player: אובייקט Player שרוצה לצפות.
        :return: True אם הצופה נוסף בהצלחה, False אם הוא כבר צופה או שחקן.
        """
        if viewer_player.user_id in self._viewers: 
            logger.debug(f"צופה {viewer_player.username} (ID: {viewer_player.user_id}) כבר צופה בשולחן {self.table_id}.") 
            return True 
        
        # ✅ ודא שהשחקן לא יושב כבר בכיסא בשולחן זה
        if viewer_player.is_seated_at_table(self.table_id): # ✅ תיקון: השתמש ב-is_seated_at_table
            logger.warning(f"שגיאה: שחקן {viewer_player.username} (ID: {viewer_player.user_id}) כבר יושב בכיסא {viewer_player.get_seat_number(self.table_id)} ולא יכול להיות צופה במקביל בשולחן {self.table_id}.") # ✅ עדכן הודעה
            return False

        self._viewers[viewer_player.user_id] = viewer_player 
        viewer_player.add_viewing_table(self.table_id) # ✅ עדכון מצב הצפייה של השחקן באובייקט Player
        logger.info(f"צופה {viewer_player.username} (ID: {viewer_player.user_id}) נוסף לרשימת הצופים של שולחן {self.table_id}.") 
        print(f"צופה {viewer_player.username} (ID: {viewer_player.user_id}) נוסף לרשימת הצופים של שולחן {self.table_id}.")
        return True

    def remove_viewer(self, user_id: int) -> bool: # שינוי player_id ל-user_id
        """
        מסיר צופה מרשימת הצופים של השולחן.
        :param user_id: ה-ID של הצופה להסרה.
        :return: True אם הצופה הוסר בהצלחה, False אחרת.
        """
        viewer_to_remove = self._viewers.pop(user_id, None)
        if viewer_to_remove:
            viewer_to_remove.remove_viewing_table(self.table_id) # ✅ עדכון מצב הצפייה של השחקן באובייקט Player
            logger.info(f"צופה עם ID {user_id} הוסר מרשימת הצופים של שולחן {self.table_id}.") 
            print(f"צופה עם ID {user_id} הוסר מרשימת הצופים של שולחן {self.table_id}.")
            return True
        logger.warning(f"שגיאה: צופה עם ID {user_id} לא נמצא ברשימת הצופים של שולחן {self.table_id}.") 
        print(f"שגיאה: צופה עם ID {user_id} לא נמצא ברשימת הצופים של שולחן {self.table_id}.")
        return False
        
    def get_all_viewers(self) -> List[Player]:
        """
        מחזירה רשימה של כל אובייקטי הצופים בשולחן.
        """
        return list(self._viewers.values())

    def get_num_viewers(self) -> int:
        """
        מחזירה את מספר הצופים בשולחן.
        """
        return len(self._viewers) # מבוסס על מספר הצופים במילון

    def get_viewer_by_id(self, user_id: int) -> Optional[Player]: # שינוי player_id ל-user_id
        """
        מחזירה אובייקט צופה לפי ה-ID שלו.
        """
        return self._viewers.get(user_id)

    # --- ניהול ידיים ---
    def start_new_hand(self) -> bool:
        """
        מתחילה יד פוקר חדשה.
        כוללת ערבוב קלפים, קביעת דילר, חלוקת בליינדים וקלפים.
        :return: True אם היד התחילה בהצלחה, False אחרת.
        """
        active_players = self.get_active_players_in_hand()
        if len(active_players) < 2:
            logger.info("אין מספיק שחקנים פעילים עם צ'יפים כדי להתחיל יד חדשה.")
            print("אין מספיק שחקנים פעילים עם צ'יפים כדי להתחיל יד חדשה.")
            self._status = TableStatus.READY_TO_START if self.num_seated_players >= 2 else TableStatus.WAITING_FOR_PLAYERS 
            if self.num_seated_players > 0 and len(active_players) == 0: 
                self._status = TableStatus.GAME_OVER
            return False
        
        self._status = TableStatus.IN_PROGRESS
        self._current_hand_number += 1
        logger.info(f"--- מתחילה יד חדשה (# {self.current_hand_number}) ---")
        print(f"\n--- מתחילה יד חדשה (# {self.current_hand_number}) ---")

        # איפוס מצב קודם
        self.pot.reset_pots() 
        self._community_cards = []
        self._deck = CardDeck() # ✅ תיקון: שינוי ל-Deck
        self._deck.shuffle()

        # איפוס מצב היד של השחקנים והגדרת מי שיושב בחוץ
        for player in self.get_seated_players():
            player.reset_hand_state(self.table_id) # ✅ העבר table_id
            if player.get_chips_on_table(self.table_id) == 0: # ✅ העבר table_id
                player.set_hand_status(self.table_id, PlayerHandStatus.SITTING_OUT) # ✅ העבר table_id
                logger.info(f"{player.username} יושב בחוץ (אין לו צ'יפים).")
                print(f"{player.username} יושב בחוץ (אין לו צ'יפים).")
            else:
                player.set_hand_status(self.table_id, PlayerHandStatus.ACTIVE) # ✅ העבר table_id

        # קביעת הדילר הבא
        self._set_next_dealer()

        # חלוקת קלפים לכל שחקן פעיל
        current_active_players_for_dealing = self.get_active_players_in_hand()
        if len(current_active_players_for_dealing) < 2: 
            logger.info("אין מספיק שחקנים פעילים לאחר חלוקת צ'יפים.")
            print("אין מספיק שחקנים פעילים לאחר חלוקת צ'יפים.")
            self._status = TableStatus.READY_TO_START if self.num_seated_players >= 2 else TableStatus.WAITING_FOR_PLAYERS 
            return False


        for player in current_active_players_for_dealing:
            hand_cards = [self._deck.deal_card(), self._deck.deal_card()] # ✅ תיקון: שינוי ל-deal()
            player.set_hand(self.table_id, hand_cards) # ✅ העבר table_id
            logger.info(f"{player.username} (כיסא {player.get_seat_number(self.table_id)}) קיבל: {hand_cards}") # ✅ העבר table_id
            print(f"{player.username} (כיסא {player.get_seat_number(self.table_id)}) קיבל: {hand_cards}") # ✅ העבר table_id

        # קביעת סדר השחקנים לפי תורות ישיבה ביחס לדילר ובליינדים
        ordered_players_for_betting = self._get_players_in_betting_order_for_round()
        
        if not ordered_players_for_betting:
            logger.info("אין שחקנים שצריכים לפעול בסבב זה. סיום יד.")
            print("אין שחקנים שצריכים לפעול בסבב זה. סיום יד.")
            self.end_hand() 
            return False

        # יצירה והפעלת סבב הימורים ראשון (Pre-flop)
        self._betting_round = BettingRound(
            active_players=ordered_players_for_betting, # סדר השחקנים לסבב
            pot=self.pot, 
            dealer_seat_index=self.current_dealer_seat_index, 
            big_blind_amount=self.big_blind 
        )
        self._betting_round.start_round(is_pre_flop=True) # יטפל בבליינדים

        if self.betting_round.status in [BettingRoundStatus.COMPLETED, BettingRoundStatus.NO_ACTIVE_PLAYERS]: 
            self._end_current_betting_round() 
            
        return True

    def _set_next_dealer(self):
        """
        קובע את מספר הכיסא של הדילר הבא.
        הדילר עובר בכיסאות פעילים (עם צ'יפים) לפי הסדר.
        """
        active_seated_players = self.get_active_players_in_hand() 
        if not active_seated_players:
            self._current_dealer_seat_index = -1
            return

        # ודא שהשחקנים ממוינים לפי מספר כיסא
        active_seated_players.sort(key=lambda p: p.get_seat_number(self.table_id)) # ✅ ודא מיון נכון

        if self.current_dealer_seat_index == -1: 
            self._current_dealer_seat_index = active_seated_players[0].get_seat_number(self.table_id) # ✅ השתמש ב-get_seat_number
        else:
            current_dealer_idx_in_active = -1
            for i, p in enumerate(active_seated_players):
                if p.get_seat_number(self.table_id) == self.current_dealer_seat_index: # ✅ השתמש ב-get_seat_number
                    current_dealer_idx_in_active = i
                    break
            
            if current_dealer_idx_in_active == -1 or current_dealer_idx_in_active == len(active_seated_players) - 1:
                self._current_dealer_seat_index = active_seated_players[0].get_seat_number(self.table_id) # ✅ השתמש ב-get_seat_number
            else:
                self._current_dealer_seat_index = active_seated_players[current_dealer_idx_in_active + 1].get_seat_number(self.table_id) # ✅ השתמש ב-get_seat_number

        logger.info(f"הדילר ביד זו הוא כיסא מספר: {self.current_dealer_seat_index}")
        print(f"הדילר ביד זו הוא כיסא מספר: {self.current_dealer_seat_index}")


    def _get_players_in_betting_order_for_round(self) -> List[Player]:
        """
        מחזירה רשימה של שחקנים פעילים ביד, מסודרים לפי סדר התור בפוקר
        (החל מהשחקן שצריך לפעול ראשון אחרי הבליינדים בפרי-פלופ, או אחרי הדילר בפוסט-פלופ).
        זו לוגיקה מורכבת שחייבת להיות מדויקת.
        """
        all_seated_players = self.get_seated_players() 
        active_players_in_hand = [p for p in all_seated_players if p.get_hand_status(self.table_id) in [PlayerHandStatus.ACTIVE, PlayerHandStatus.ALL_IN]] # ✅ העבר table_id

        if not active_players_in_hand:
            return []

        # ודא שהשחקנים ממוינים לפי מספר כיסא
        active_players_in_hand.sort(key=lambda p: p.get_seat_number(self.table_id)) # ✅ ודא מיון נכון

        dealer_pos_in_seated = -1
        for i, p in enumerate(all_seated_players):
            if p.get_seat_number(self.table_id) == self.current_dealer_seat_index: # ✅ השתמש ב-get_seat_number
                dealer_pos_in_seated = i
                break

        if dealer_pos_in_seated == -1: 
            # אם הדילר לא נמצא ב-active_players_in_hand, זה מצב חריג, נחזיר את כולם
            return active_players_in_hand 

        if len(self.community_cards) > 0 or self.current_hand_number > 0 : # פוסט-פלופ
            # השחקן הראשון לפעול בפוסט-פלופ הוא השחקן הפעיל הראשון משמאל לדילר
            first_to_act_index_in_seated = (dealer_pos_in_seated + 1) % len(all_seated_players) 
            
            first_player_to_act_index = -1
            num_seated = len(all_seated_players)
            for _ in range(num_seated):
                current_player = all_seated_players[first_to_act_index_in_seated]
                if current_player.get_hand_status(self.table_id) in [PlayerHandStatus.ACTIVE, PlayerHandStatus.ALL_IN]: # ✅ העבר table_id
                    first_player_to_act_index = first_to_act_index_in_seated
                    break
                first_to_act_index_in_seated = (first_to_act_index_in_seated + 1) % num_seated
            
            if first_player_to_act_index == -1: 
                return [] 
                
            ordered_for_round = []
            current_idx = first_player_to_act_index
            while True:
                player = all_seated_players[current_idx]
                if player.get_hand_status(self.table_id) in [PlayerHandStatus.ACTIVE, PlayerHandStatus.ALL_IN]: # ✅ העבר table_id
                    ordered_for_round.append(player)
                current_idx = (current_idx + 1) % num_seated
                if current_idx == first_player_to_act_index: 
                    break
            
            return ordered_for_round
            
        else: # Pre-Flop
            # בפרי-פלופ, השחקן הראשון לפעול הוא ה-UTG (Under The Gun)
            # שהוא השחקן הפעיל הראשון משמאל לביג בליינד.
            # לוגיקה זו מורכבת יותר ודורשת זיהוי סמול/ביג בליינדים.
            # לצורך פשטות זמנית, נחזיר את כל השחקנים הפעילים בסדר הכיסאות.
            # TODO: יש ליישם לוגיקה מדויקת של UTG.
            return [p for p in active_players_in_hand] # כבר ממוינים לפי כיסא


    def _open_community_cards(self, num_cards: int):
        """
        פותח קלפי קהילה (Flop, Turn, River).
        :param num_cards: מספר הקלפים לפתוח (3 עבור פלופ, 1 עבור טרן/ריבר).
        """
        if len(self._deck.get_cards()) < num_cards + 1: 
            logger.warning("אין מספיק קלפים בחפיסה לפתוח קלפי קהילה נוספים.")
            print("אין מספיק קלפים בחפיסה לפתוח קלפי קהילה נוספים.")
            return

        self._deck.deal_card() # ✅ תיקון: "שורף" קלף לפני כל פתיחה (שינוי ל-deal())
        
        for _ in range(num_cards):
            self._community_cards.append(self._deck.deal()) # ✅ תיקון: שינוי ל-deal()
        
        logger.info(f"קלפי קהילה: {self.community_cards}")
        print(f"קלפי קהילה: {self.community_cards}")

    def process_player_action(self, player_id: int, action: PlayerAction, amount: Optional[float] = None) -> bool: # שינוי amount ל-float
        """
        מעבד פעולת שחקן שמגיעה מהלקוח.
        מעביר את הפעולה לאובייקט BettingRound הנוכחי.

        :param player_id: ה-ID של השחקן.
        :param action: סוג הפעולה.
        :param amount: סכום ההימור (אם רלוונטי).
        :return: True אם הפעולה בוצעה, False אחרת.
        """
        if self.status != TableStatus.IN_PROGRESS or not self.betting_round: 
            logger.warning(f"שגיאה: לא ניתן לבצע פעולה כשהשולחן במצב {self.status.value} או שאין סבב הימורים פעיל.") 
            print(f"שגיאה: לא ניתן לבצע פעולה כשהשולחן במצב {self.status.value} או שאין סבב הימורים פעיל.")
            return False

        current_player = self.betting_round.current_player 
        if not current_player or current_player.user_id != player_id: 
            logger.warning(f"שגיאה: זה לא תורו של שחקן {player_id} לפעול.")
            print(f"שגיאה: זה לא תורו של שחקן {player_id} לפעול.")
            return False

        # ✅ העבר את אובייקט ה-Player ואת ה-table_id למתודה process_action של BettingRound
        success = self.betting_round.process_action(current_player, action, amount, self.table_id) 
        
        if success and (self.betting_round.status == BettingRoundStatus.COMPLETED or \
           self.betting_round.status == BettingRoundStatus.NO_ACTIVE_PLAYERS): 
            self._end_current_betting_round() 
            
        return success

    def _end_current_betting_round(self):
        """
        מסיימת את סבב ההימורים הנוכחי ואוספת את הכסף לקופה.
        """
        if not self.betting_round: 
            return

        self.betting_round.end_round_and_collect_bets() 
        self._betting_round = None 

        self._advance_hand_phase()


    def _advance_hand_phase(self):
        """
        מקדם את שלב היד (Pre-flop -> Flop -> Turn -> River -> Showdown).
        """
        active_players_count = len(self.get_active_players_in_hand())
        if active_players_count <= 1:
            self._determine_winner_and_distribute_pot(skip_showdown=True)
            return

        current_community_cards_count = len(self.community_cards) 

        if current_community_cards_count == 0: 
            logger.info("\n--- שלב FLOP ---")
            print("\n--- שלב FLOP ---")
            self._open_community_cards(3) 
            self._start_new_betting_round()
        elif current_community_cards_count == 3: 
            logger.info("\n--- שלב TURN ---")
            print("\n--- שלב TURN ---")
            self._open_community_cards(1) 
            self._start_new_betting_round()
        elif current_community_cards_count == 4: 
            logger.info("\n--- שלב RIVER ---")
            print("\n--- שלב RIVER ---")
            self._open_community_cards(1) 
            self._start_new_betting_round()
        elif current_community_cards_count == 5: 
            logger.info("\n--- שלב SHOWDOWN ---")
            print("\n--- שלב SHOWDOWN ---")
            self._determine_winner_and_distribute_pot()
        else:
            logger.warning("שגיאה: שלב יד לא ידוע או לא תקין.")
            print("שגיאה: שלב יד לא ידוע או לא תקין.")
            self.end_hand() 


    def _start_new_betting_round(self):
        """
        מתחילה סבב הימורים חדש לאחר פתיחת קלפי קהילה.
        """
        active_players_for_round = self._get_players_in_betting_order_for_round() 
        
        if len(active_players_for_round) < 2:
            self._determine_winner_and_distribute_pot(skip_showdown=True)
            return

        self._betting_round = BettingRound(
            active_players=active_players_for_round, 
            pot=self.pot, 
            dealer_seat_index=self.current_dealer_seat_index, 
            big_blind_amount=self.big_blind 
        )
        self._betting_round.start_round(is_pre_flop=False) 
        
        if self.betting_round.status in [BettingRoundStatus.COMPLETED, BettingRoundStatus.NO_ACTIVE_PLAYERS]: 
            self._end_current_betting_round() 


    def _determine_winner_and_distribute_pot(self, skip_showdown: bool = False):
        """
        קובעת את המנצח (או מנצחים) ומחלקת את הקופה.
        :param skip_showdown: True אם רק שחקן אחד נשאר (אז אין Showdown).
        """
        logger.info("\n--- קביעת זוכה וחלוקת קופה ---")
        print("\n--- קביעת זוכה וחלוקת קופה ---")
        
        # לוגיקה זו חייבת לכלול טיפול בקופות צדדיות (Side Pots)
        # שכרגע לא ממומש במלואו במחלקת Pot.
        # זהו אחד החלקים המורכבים ביותר בסימולציית פוקר.
        # כרגע, נתמקד בחלוקה פשוטה של הקופה הראשית.

        # שלב 1: זיהוי שחקנים רלוונטיים (אלה שנותרו ביד)
        players_in_showdown = [p for p in self.get_seated_players() if p.get_hand_status(self.table_id) in [PlayerHandStatus.ACTIVE, PlayerHandStatus.ALL_IN]] # ✅ העבר table_id
        
        if skip_showdown and len(players_in_showdown) == 1:
            winner = players_in_showdown[0]
            winnings = self.pot.get_total_pot_size() # ✅ תיקון: קבל את סכום הקופה
            winner.add_chips_to_table(self.table_id, winnings) # ✅ העבר table_id
            logger.info(f"שחקן {winner.username} ניצח את הקופה בסך {winnings} צ'יפים (היד הסתיימה מוקדם).")
            print(f"שחקן {winner.username} ניצח את הקופה בסך {winnings} צ'יפים (היד הסתיימה מוקדם).")
            self.end_hand()
            return

        if not players_in_showdown:
            logger.warning("אין שחקנים פעילים להכרעת זוכה.")
            print("אין שחקנים פעילים להכרעת זוכה.")
            self.end_hand()
            return

        # שלב 2: דירוג ידיים
        # יצירת רשימת ידיים לדירוג
        hands_to_evaluate = []
        for player in players_in_showdown:
            # ודא שלשחקן יש קלפים ביד
            if player.get_hand(self.table_id): # ✅ העבר table_id
                hands_to_evaluate.append({
                    'player_id': player.user_id,
                    'player_name': player.username,
                    'hand_cards': player.get_hand(self.table_id), # ✅ העבר table_id
                    'community_cards': self.community_cards
                })
            else:
                logger.warning(f"שחקן {player.username} (ID: {player.user_id}) ללא קלפים ביד בשלב ה-Showdown.")

        if not hands_to_evaluate:
            logger.warning("אין ידיים לדירוג בשלב ה-Showdown.")
            print("אין ידיים לדירוג בשלב ה-Showdown.")
            self.end_hand()
            return

        # קריאה ל-HandEvaluator
        ranked_hands = self._hand_evaluator.rank_hands(hands_to_evaluate)

        if not ranked_hands:
            logger.error("HandEvaluator לא החזיר ידיים מדורגות.")
            print("HandEvaluator לא החזיר ידיים מדורגות.")
            self.end_hand()
            return

        # שלב 3: חלוקת קופות צדדיות (Side Pots) - לוגיקה מורכבת
        # לצורך פשטות כרגע, נתייחס רק לקופה הראשית.
        
        # מציאת היד הטובה ביותר (או הטובות ביותר במקרה של תיקו)
        best_rank = ranked_hands[0]['rank_value']
        winning_hands = [h for h in ranked_hands if h['rank_value'] == best_rank]

        if len(winning_hands) == 1:
            # זוכה יחיד
            winner_info = winning_hands[0]
            winner_player = self.get_player_by_id(winner_info['player_id'])
            if winner_player:
                winnings = self.pot.get_total_pot_size() # ✅ תיקון: קבל את סכום הקופה
                winner_player.add_chips_to_table(self.table_id, winnings) # ✅ העבר table_id
                logger.info(f"שחקן {winner_player.username} ניצח את הקופה בסך {winnings} צ'יפים עם {winner_info['hand_name']}.")
                print(f"שחקן {winner_player.username} ניצח את הקופה בסך {winnings} צ'יפים עם {winner_info['hand_name']}.")
            else:
                logger.error(f"זוכה עם ID {winner_info['player_id']} לא נמצא כאובייקט Player.")
        else:
            # תיקו בין מספר שחקנים
            num_winners = len(winning_hands)
            split_amount = self.pot.get_total_pot_size() // num_winners # ✅ תיקון: קבל את סכום הקופה
            logger.info(f"תיקו בין {num_winners} שחקנים. כל אחד מקבל {split_amount} צ'יפים.")
            print(f"תיקו בין {num_winners} שחקנים. כל אחד מקבל {split_amount} צ'יפים.")
            for winner_info in winning_hands:
                winner_player = self.get_player_by_id(winner_info['player_id'])
                if winner_player:
                    winner_player.add_chips_to_table(self.table_id, split_amount) # ✅ העבר table_id
                    logger.info(f"שחקן {winner_player.username} קיבל {split_amount} צ'יפים (תיקו עם {winner_info['hand_name']}).")
                    print(f"שחקן {winner_player.username} קיבל {split_amount} צ'יפים (תיקו עם {winner_info['hand_name']}).")
                else:
                    logger.error(f"זוכה עם ID {winner_info['player_id']} לא נמצא כאובייקט Player.")
            # טיפול בשארית אם יש
            remainder = self.pot.get_total_pot_size() % num_winners # ✅ תיקון: קבל את סכום הקופה
            if remainder > 0:
                logger.info(f"נותרו {remainder} צ'יפים בקופה (שארית מתיקו).")
                print(f"נותרו {remainder} צ'יפים בקופה (שארית מתיקו).")
                # TODO: לטפל בשארית - לרוב הולך לשחקן הראשון משמאל לדילר.

        self.end_hand()

    def end_hand(self):
        """
        מסיים את היד הנוכחית ומכין את השולחן ליד הבאה.
        """
        logger.info("--- סיום יד ---")
        print("--- סיום יד ---")
        self._community_cards = []
        self._deck = Deck() # ✅ תיקון: שינוי ל-Deck
        self.pot.reset_pots()
        self._betting_round = None

        # איפוס מצב היד של כל השחקנים היושבים
        for player in self.get_seated_players():
            player.reset_hand_state(self.table_id) # ✅ העבר table_id
            # אם שחקן יושב בחוץ, הוא נשאר כך. אם פעיל, הוא ממתין ליד הבאה.
            if player.get_chips_on_table(self.table_id) == 0: # ✅ העבר table_id
                player.set_hand_status(self.table_id, PlayerHandStatus.SITTING_OUT) # ✅ העבר table_id
            else:
                player.set_hand_status(self.table_id, PlayerHandStatus.WAITING_FOR_NEW_HAND) # ✅ העבר table_id

        if self.num_seated_players < 2:
            self._status = TableStatus.WAITING_FOR_PLAYERS
        else:
            self._status = TableStatus.READY_TO_START
        logger.info(f"שולחן {self.name} כעת במצב: {self.status.value}.")
        print(f"שולחן {self.name} כעת במצב: {self.status.value}.")

    def to_dict(self, requesting_player_id: Optional[int] = None) -> Dict[str, Any]:
        """ממיר את אובייקט ה-Table למילון לייצוג ב-JSON."""
        players_data = []
        for player_obj in self._players.values(): 
            players_data.append(player_obj.to_dict(
                include_private_data=(player_obj.user_id == requesting_player_id),
                table_id=self.table_id # ✅ העבר table_id ל-Player.to_dict
            ))

        viewers_data = []
        for viewer_obj in self._viewers.values(): 
            viewers_data.append(viewer_obj.to_dict(
                include_private_data=False,
                table_id=self.table_id # ✅ העבר table_id ל-Player.to_dict
            ))

        # ✅ הוספת לוג לבדיקת תוכן ה-pot לאחר to_dict()
        pot_dict_representation = self.pot.to_dict()
        logger.debug(f"Pot object converted to dict: {pot_dict_representation}")

        return {
            'table_id': self.table_id,
            'name': self.name, 
            'max_players': self.max_players,
            'small_blind': self.small_blind,
            'big_blind': self.big_blind,
            'status': self.status.value, 
            'players': players_data,
            'viewers': viewers_data, 
            'community_cards': [card.to_dict() for card in self.community_cards],
            'pot': pot_dict_representation, 
            'current_betting_round_status': self.betting_round.status.value if self.betting_round else "None", 
            'is_game_started': self.status == TableStatus.IN_PROGRESS, 
            'current_dealer_seat_index': self.current_dealer_seat_index,
            'current_hand_number': self.current_hand_number, 
            # 'current_player_to_act_id': self.betting_round.current_player.user_id if self.betting_round and self.betting_round.current_player else None, 
            # 'min_raise_amount': self.betting_round.min_raise_amount if self.betting_round else 0,
            # 'last_bet_amount': self.betting_round.last_bet_amount if self.betting_round else 0,
        }
