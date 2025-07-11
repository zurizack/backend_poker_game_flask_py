from typing import List, Dict, Optional, Tuple
import enum

# ייבוא מחלקות קודמות
from backend.poker_server.game.engine.player_oop import Player
from backend.poker_server.game.engine.pot import Pot # נצטרך את Pot כדי להעביר אליו הימורים
from backend.poker_server.game.engine.player_hand import PlayerAction, PlayerHandStatus # לצורך סטטוסים ופעולות של שחקן


class BettingRoundStatus(enum.Enum):
    """
    סטטוסים אפשריים לסבב הימורים.
    """
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NO_ACTIVE_PLAYERS = "no_active_players" # כל השחקנים קיפלו חוץ מאחד


class BettingRound:
    """
    מחלקה שמנהלת סבב הימורים יחיד במשחק פוקר (לדוגמה: Pre-flop, Flop, Turn, River).
    """
    def __init__(self, active_players: List[Player], pot: Pot, dealer_seat_index: int, big_blind_amount: int):
        """
        קונסטרוקטור למחלקת BettingRound.

        :param active_players: רשימה של אובייקטי Player פעילים (שלא קיפלו או יושבים בחוץ) בתחילת הסבב.
                               הרשימה צריכה להיות מסודרת לפי תורות ישיבה בשולחן, החל מהשחקן הראשון בתור.
        :param pot: אובייקט Pot המנהל את קופת המשחק.
        :param dealer_seat_index: אינדקס הכיסא של הדילר. משמש לקביעת סדר הפעולות.
        :param big_blind_amount: גובה הביג בליינד. משמש לקביעת ההימור המינימלי.
        """
        if not active_players:
            raise ValueError("סבב הימורים חייב להתחיל עם שחקנים פעילים.")
        
        self._active_players: List[Player] = active_players
        self._pot: Pot = pot
        self._dealer_seat_index: int = dealer_seat_index # אינדקס הכיסא של הדילר
        self._big_blind_amount: int = big_blind_amount

        # מצב הסבב
        self._status: BettingRoundStatus = BettingRoundStatus.IN_PROGRESS
        
        # ההימור הגבוה ביותר ששולם על ידי שחקן כלשהו בסבב הנוכחי.
        # מתחיל ב-0, או בביג בליינד בסיבוב הפרי-פלופ.
        self._current_max_bet_in_round: int = 0 
        
        # אינדקס השחקן הנוכחי בתור בתוך רשימת _active_players.
        self._current_player_index: int = 0 
        
        # כמות ההימורים של כל שחקן *בסבב הנוכחי* (לא מצטבר)
        self._player_round_bets: Dict[str, int] = {p.get_user_id(): 0 for p in active_players}

        # מישהו כבר ביצע רייז/הימור בסבב זה?
        self._raised_this_round: bool = False
        
        # ההפרש בין ההימור הגבוה ביותר לבין ההימור השני בגובהו, או הביג בליינד.
        # זה הערך של "גובה הרייז" האחרון.
        self._last_raise_amount: int = self._big_blind_amount # ברירת מחדל
        
        # שחקנים שעדיין צריכים לפעול (לדוגמה: אחרי רייז).
        # נשמור את ה-user_id שלהם.
        self._players_to_act: List[str] = [p.get_user_id() for p in active_players]
        # נשמור את נקודת ההתחלה של סבב הפעולות (מי התחיל את הסבב/רייז האחרון)
        self._round_starter_id: Optional[str] = None 
        
        # סך ההימור ששחקן השקיע ביד כולה (לא רק בסבב זה)
        # נצטרך לקבל את זה מה-Player עצמו או לנהל כאן
        # כרגע, נשתמש ב-player.get_current_bet() המצטבר.

    def start_round(self, is_pre_flop: bool = False):
        """
        מתחילה את סבב ההימורים.
        מטפלת בבליינדים במידת הצורך.
        """
        print(f"מתחיל סבב הימורים חדש. שחקנים פעילים: {[p.get_username() for p in self._active_players]}")

        if is_pre_flop:
            # בפרי-פלופ, הבליינדים הם ההימורים הראשונים
            self._handle_blinds()
        
        # קביעת השחקן הראשון לפעול
        self._set_first_player_to_act()
        self._round_starter_id = self._active_players[self._current_player_index].get_user_id()
        self._status = BettingRoundStatus.IN_PROGRESS

        if len(self._active_players) == 1:
            self._status = BettingRoundStatus.NO_ACTIVE_PLAYERS # אם נשאר רק שחקן אחד, הסבב הסתיים.


    def _handle_blinds(self):
        """
        מטפלת בהימורי הבליינדים בתחילת הפרי-פלופ.
        (הנחה: השחקנים ברשימת _active_players מסודרים אחרי הדילר,
        וכך ה-Small Blind וה-Big Blind ימוקמו נכון).
        """
        # TODO: Implement accurate blind posting logic.
        # This requires knowing the positions (SB, BB) based on dealer position.
        # For now, a simplified example:
        if len(self._active_players) >= 2:
            # נניח שהשחקן הבא אחרי הדילר הוא ה-SB והבא אחריו הוא ה-BB.
            # זה דורש לוגיקה שתמצא את ה-SB/BB האמיתיים.
            # כרגע, ניקח פשוט את 2 השחקנים הראשונים בתור (לא בהכרח נכון לפוקר אמיתי)

            # נניח ש-active_players כבר מסודר לפי תור, כולל בליינדים בהתחלה
            
            # Small Blind
            sb_player = self._active_players[0]
            sb_amount = self._big_blind_amount // 2
            if sb_player.can_afford(sb_amount):
                sb_player.remove_chips_from_table(sb_amount)
                sb_player.add_to_current_bet(sb_amount) # מוסיף להימור הכולל ביד
                self._player_round_bets[sb_player.get_user_id()] += sb_amount
                # self._pot.add_bet(sb_player, sb_amount, self._current_max_bet_in_round) # Add to pot in collect_round_bets
                print(f"{sb_player.get_username()} שם סמול בליינד: {sb_amount}")
            else:
                # הלך אול-אין על הסמול בליינד
                sb_player.go_all_in()
                sb_amount = sb_player.get_current_bet() # הסכום האמיתי שהכניס
                self._player_round_bets[sb_player.get_user_id()] += sb_amount
                print(f"{sb_player.get_username()} הלך אול-אין על סמול בליינד: {sb_amount}")
            
            # Big Blind
            if len(self._active_players) >= 2:
                bb_player = self._active_players[1]
                bb_amount = self._big_blind_amount
                if bb_player.can_afford(bb_amount):
                    bb_player.remove_chips_from_table(bb_amount)
                    bb_player.add_to_current_bet(bb_amount) # מוסיף להימור הכולל ביד
                    self._player_round_bets[bb_player.get_user_id()] += bb_amount
                    # self._pot.add_bet(bb_player, bb_amount, self._current_max_bet_in_round)
                    print(f"{bb_player.get_username()} שם ביג בליינד: {bb_amount}")
                else:
                    # הלך אול-אין על הביג בליינד
                    bb_player.go_all_in()
                    bb_amount = bb_player.get_current_bet()
                    self._player_round_bets[bb_player.get_user_id()] += bb_amount
                    print(f"{bb_player.get_username()} הלך אול-אין על ביג בליינד: {bb_amount}")
                
                # עדכון ההימור המקסימלי בסבב
                self._current_max_bet_in_round = max(self._current_max_bet_in_round, bb_amount)
        
        # לאחר הבליינדים, נאסוף את ההימורים לקופה
        self._pot.collect_round_bets(self._player_round_bets, {p.get_user_id(): p.get_current_bet() for p in self._active_players})
        self._player_round_bets = {p.get_user_id(): 0 for p in self._active_players} # איפוס הימורים לסבב


    def _set_first_player_to_act(self):
        """
        קובעת את השחקן הראשון לפעול בסבב.
        בפרי-פלופ, זה השחקן שממוקם לאחר הביג בליינד.
        בסבבים הבאים, זה השחקן הראשון הפעיל לאחר הדילר (או הדילר עצמו אם הוא פעיל).
        """
        # TODO: Implement accurate first player logic for each round type.
        # This is complex as it depends on dealer position and active players.
        
        # לבינתיים, נניח שהשחקנים כבר מסודרים בתור,
        # ובפרי-פלופ נתחיל מ-index 2 (אחרי SB ו-BB, אם קיימים).
        # בפוסט-פלופ נתחיל מהראשון ברשימת השחקנים הפעילים.

        if len(self._active_players) > 0:
            # בפרי-פלופ, מיקום השחקן הראשון אחרי הבליינדים
            # בפוסט-פלופ, מיקום השחקן הראשון הפעיל אחרי הדילר (הכפתור)
            self._current_player_index = 0 # נתחיל מהראשון ברשימה לבינתיים

            # יש לוודא שה- _active_players מסודר לפי סדר התור הנכון לפני העברה למחלקה
            # זה יהיה באחריות מחלקת Table.
            
            # מציאת מיקום הדילר ברשימת השחקנים הפעילים
            dealer_active_index = -1
            for i, p in enumerate(self._active_players):
                if p.get_seat_number() == self._dealer_seat_index:
                    dealer_active_index = i
                    break

            if dealer_active_index != -1:
                # בפוסט-פלופ, התור מתחיל מהשחקן הפעיל הראשון אחרי הדילר
                # או מהדילר עצמו אם כולם קיפלו אחריו והוא השחקן היחיד שנשאר
                # ה-index של מי שצריך לפעול יהיה (dealer_active_index + 1) % len(self._active_players)
                # ולחפש את השחקן הפעיל הראשון משם
                
                # לבינתיים, נשאיר פשוט 0. (זו נקודה שדורשת טיפול פרטני)
                pass


    def get_current_player(self) -> Optional[Player]:
        """
        מחזירה את אובייקט השחקן שהתור שלו לפעול.
        """
        if self._status != BettingRoundStatus.IN_PROGRESS or not self._active_players:
            return None
        
        # לוודא שהאינדקס תקין
        if 0 <= self._current_player_index < len(self._active_players):
            return self._active_players[self._current_player_index]
        return None

    def get_current_max_bet(self) -> int:
        """
        מחזירה את סכום ההימור המקסימלי שהוצב בסבב זה עד כה.
        """
        return self._current_max_bet_in_round

    def get_call_amount(self, player: Player) -> int:
        """
        מחזירה את הסכום שהשחקן צריך להשלים כדי לבצע CALL.
        :param player: אובייקט השחקן.
        """
        # הסכום שהשחקן כבר שם ביד כולה
        player_total_bet = player.get_current_bet()
        
        # הסכום שצריך להשלים הוא ההימור המקסימלי פחות מה שהשחקן כבר שם
        amount_to_call = self._current_max_bet_in_round - player_total_bet
        
        # אם הסכום שלילי (כבר הימר יותר), או אפס, אז אין CALL.
        return max(0, amount_to_call)

    def get_min_raise_amount(self) -> int:
        """
        מחזירה את סכום הרייז המינימלי המותר.
        זהו לרוב הביג בליינד, או גובה הרייז האחרון אם הוא היה גדול יותר.
        """
        return max(self._big_blind_amount, self._last_raise_amount)

    def process_action(self, player_id: str, action: PlayerAction, amount: Optional[int] = None) -> bool:
        """
        מעבדת פעולה של שחקן בסבב ההימורים.

        :param player_id: ה-ID של השחקן המבצע את הפעולה.
        :param action: פעולת השחקן (CHECK, CALL, RAISE, FOLD, ALL_IN).
        :param amount: סכום ההימור (רלוונטי עבור RAISE).
        :return: True אם הפעולה בוצעה בהצלחה, False אחרת.
        """
        current_player = self.get_current_player()
        if not current_player or current_player.get_user_id() != player_id:
            print(f"שגיאה: זה לא תורו של שחקן {player_id} לפעול.")
            return False

        # לא ניתן לפעול אם השחקן כבר קיפל או באול-אין
        if current_player.get_hand_status() in [PlayerHandStatus.FOLDED, PlayerHandStatus.ALL_IN]:
            print(f"שגיאה: שחקן {current_player.get_username()} כבר במצב {current_player.get_hand_status().value}.")
            return False

        current_player_total_bet_in_hand = current_player.get_current_bet() # הסכום הכולל ששם השחקן ביד
        amount_to_call = self._current_max_bet_in_round - current_player_total_bet_in_hand
        
        print(f"{current_player.get_username()} מנסה לבצע פעולה: {action.value} עם סכום: {amount if amount is not None else 'N/A'}")

        if action == PlayerAction.FOLD:
            current_player.fold()
            print(f"{current_player.get_username()} קיפל את היד.")
            
        elif action == PlayerAction.CHECK:
            if amount_to_call > 0:
                print(f"שגיאה: לא ניתן לבצע CHECK כאשר יש הימור להשוות ({amount_to_call} צ'יפים).")
                return False
            current_player.set_last_action(PlayerAction.CHECK)
            print(f"{current_player.get_username()} עשה CHECK.")
            
        elif action == PlayerAction.CALL:
            if not current_player.can_afford(amount_to_call):
                print(f"שגיאה: {current_player.get_username()} לא יכול להשלים ל-CALL. חסרים לו {amount_to_call - current_player.get_chips_on_table()} צ'יפים.")
                return False
            
            # הסרת צ'יפים מערימת השחקן והוספה להימור שלו ביד
            current_player.remove_chips_from_table(amount_to_call)
            current_player.add_to_current_bet(amount_to_call)
            self._player_round_bets[player_id] += amount_to_call # רשום כמה שם בסבב זה
            current_player.set_last_action(PlayerAction.CALL)
            print(f"{current_player.get_username()} השווה (CALL) ל-{self._current_max_bet_in_round}.")

        elif action == PlayerAction.BET or action == PlayerAction.RAISE:
            if amount is None or amount <= 0:
                print("שגיאה: סכום ההימור/רייז חייב להיות חיובי.")
                return False

            if action == PlayerAction.BET and self._current_max_bet_in_round > 0:
                print("שגיאה: לא ניתן לבצע BET כאשר כבר קיים הימור. השתמש ב-RAISE.")
                return False
            
            # הסכום הכולל של השחקן אם הוא יבצע את הפעולה (הימור נוכחי ביד + סכום הפעולה הנוכחית)
            total_bet_if_actioned = current_player_total_bet_in_hand + amount

            # בדיקות חוקיות עבור BET/RAISE
            # 1. האם יש לו מספיק צ'יפים?
            if not current_player.can_afford(amount):
                print(f"שגיאה: {current_player.get_username()} לא יכול להרשות לעצמו להמר/לעלות ב-{amount} צ'יפים.")
                return False
            
            # 2. האם ההימור החדש גבוה יותר מההימור המקסימלי הנוכחי?
            #    (למעט אם זה אול-אין בפחות)
            if total_bet_if_actioned < self._current_max_bet_in_round:
                print(f"שגיאה: ההימור החדש ({total_bet_if_actioned}) נמוך מההימור הנוכחי ({self._current_max_bet_in_round}).")
                return False

            # 3. האם הרייז מספיק גדול?
            #    ההפרש בין ההימור החדש להימור המקסימלי הנוכחי (זהו גודל הרייז בפועל)
            actual_raise_amount = total_bet_if_actioned - self._current_max_bet_in_round
            min_raise_required = self.get_min_raise_amount()

            if actual_raise_amount < min_raise_required and current_player.get_chips_on_table() > amount:
                print(f"שגיאה: הרייז קטן מדי. מינימום רייז הוא {min_raise_required} צ'יפים. הרייז שלך: {actual_raise_amount}.")
                return False

            # הסרת צ'יפים ועדכון הימור השחקן
            current_player.remove_chips_from_table(amount)
            current_player.add_to_current_bet(amount)
            self._player_round_bets[player_id] += amount

            # עדכון ההימור המקסימלי בסבב וגובה הרייז האחרון
            if total_bet_if_actioned > self._current_max_bet_in_round:
                self._last_raise_amount = total_bet_if_actioned - self._current_max_bet_in_round # גודל הרייז בפועל
                self._current_max_bet_in_round = total_bet_if_actioned
                self._raised_this_round = True
                self._round_starter_id = player_id # מי שביצע רייז הוא נקודת העצירה הבאה
                print(f"{current_player.get_username()} ביצע RAISE ל-{self._current_max_bet_in_round} (הימור כולל ביד: {current_player.get_current_bet()}).")
                
            current_player.set_last_action(action)
            
        elif action == PlayerAction.ALL_IN:
            # שחקן הולך אול-אין
            all_in_amount_from_chips = current_player.get_chips_on_table() # כמה צ'יפים נותרו לו בכיסא
            
            # לוגיקת ה-All-In ב-Player אמורה לטפל בהעברת כל הצ'יפים מהכיסא להימור הכולל ביד
            current_player.go_all_in() 
            
            # הסכום הכולל שהשחקן הכניס ביד כעת (לאחר ה-all-in)
            player_total_bet_in_hand_after_all_in = current_player.get_current_bet()

            # אם ה-All-In הזה גבוה מההימור המקסימלי הנוכחי, זה נחשב כרייז
            if player_total_bet_in_hand_after_all_in > self._current_max_bet_in_round:
                self._last_raise_amount = player_total_bet_in_hand_after_all_in - self._current_max_bet_in_round # גודל ה"רייז" של האול-אין
                self._current_max_bet_in_round = player_total_bet_in_hand_after_all_in
                self._raised_this_round = True 
                self._round_starter_id = player_id # All-in גם מאפס את תור הפעולות
            
            # כמה צ'יפים הוא הוסיף בסבב זה, מתוך ה-All-In
            # זהו ההפרש בין סך ההימור שלו ביד כעת לבין סך ההימור שלו לפני ה-All-In הזה
            # (או פשוט כמה צ'יפים היו לו בכיסא לפני הפעולה, במידה והוא לא היה ב-ALL-IN חלקי)
            self._player_round_bets[player_id] += all_in_amount_from_chips # נוסיף כמה צ'יפים חדשים הכניס לסבב
            
            print(f"{current_player.get_username()} הלך ALL-IN עם {all_in_amount_from_chips} צ'יפים (סה\"כ ביד: {player_total_bet_in_hand_after_all_in}).")

        else:
            print(f"פעולה לא חוקית: {action.value}")
            return False

        # מעבר לשחקן הבא לאחר פעולה מוצלחת
        self._advance_to_next_player()
        self._check_round_completion()
        
        return True

    def _advance_to_next_player(self):
        """
        מקדם את התור לשחקן הפעיל הבא.
        מדלג על שחקנים שקיפלו או באול-אין.
        """
        num_players = len(self._active_players)
        if num_players == 0:
            self._status = BettingRoundStatus.NO_ACTIVE_PLAYERS
            return

        original_index = self._current_player_index
        # מציאת מיקום ה-round_starter_id הנוכחי ברשימת השחקנים הפעילים
        current_round_starter_player = next((p for p in self._active_players if p.get_user_id() == self._round_starter_id), None)
        
        # אם אין מי שהתחיל את הסבב, או שהשחקן הנוכחי הוא האחרון וכולם השוו
        if current_round_starter_player is None: # או במצב שהסבב התחיל ואין רייז, אז אין "מחדש"
             pass # תמשיך כרגיל, ה-check_round_completion יקבע סיום

        while True:
            self._current_player_index = (self._current_player_index + 1) % num_players
            next_player = self._active_players[self._current_player_index]

            # תנאי עצירה: הגענו חזרה למי שהתחיל את הסבב / ביצע את הרייז האחרון
            # וכל השחקנים ביניהם כבר פעלו, השוו או עשו אול-אין.
            if next_player.get_user_id() == self._round_starter_id:
                # יש לבדוק האם כולם השוו או הלכו אול-אין
                all_matched_or_all_in = True
                for p in self._active_players: # נבדוק את כולם
                    if p.get_hand_status() == PlayerHandStatus.ACTIVE and p.get_current_bet() < self._current_max_bet_in_round:
                        all_matched_or_all_in = False
                        break
                
                if all_matched_or_all_in:
                    # כל השחקנים הפעילים (שלא קיפלו) השוו את ההימור המקסימלי או הלכו אול-אין.
                    # והתור חזר לנקודת ההתחלה של הסבב/רייז האחרון.
                    # זהו תנאי לסיום הסבב.
                    break 
                
            # רק שחקנים פעילים (לא מקופלים, לא יושבים בחוץ) צריכים לפעול
            # שחקן ALL_IN לא צריך לפעול שוב
            if next_player.get_hand_status() == PlayerHandStatus.ACTIVE:
                # אם שחקן פעיל ועדיין לא השווה את ההימור המקסימלי, זה התור שלו
                if next_player.get_current_bet() < self._current_max_bet_in_round:
                    return # נמצא שחקן שצריך לפעול
                elif next_player.get_current_bet() == self._current_max_bet_in_round and self._raised_this_round:
                    # אם היה רייז בסבב, ושחקן השווה אבל התור שלו שוב כי מישהו אחר העלה אחריו
                    # והוא לא ה-round_starter_id, אז הוא צריך לפעול.
                    # אבל אם הוא ה-round_starter_id, אז הסבב הסתיים.
                    pass # הלוגיקה של round_starter_id כבר תפסה למעלה
                else: # current_max_bet_in_round == 0 או שהשחקן כבר השווה (ולא היה רייז אחריו)
                    pass # ממשיכים לחפש

            # אם עברנו על כולם וכל השחקנים ה"פעילים" השוו, או קיפלו, או אול-אין (וכבר לא צריכים לפעול),
            # והגענו חזרה לנקודת ההתחלה, הסבב הסתיים.
            # הלוגיקה שלמעלה עם next_player.get_user_id() == self._round_starter_id אמורה לטפל בזה.
            # אם הגענו לכאן בלי למצוא שחקן לפעול, זה סימן שהסבב הסתיים.
            # זה מטופל ב-check_round_completion.

    def _check_round_completion(self):
        """
        בודקת האם סבב ההימורים הסתיים.
        הסבב מסתיים כאשר:
        1. כל השחקנים למעט אחד קיפלו (אז השחקן שנותר זוכה בקופה).
        2. כל השחקנים הפעילים השוו את ההימור המקסימלי הנוכחי,
           והתור חזר לשחקן שהתחיל את סבב הפעולות (או שביצע את הרייז האחרון).
           (למעט שחקנים שהלכו אול-אין בפחות).
        """
        active_players_in_round = [p for p in self._active_players 
                                 if p.get_hand_status() == PlayerHandStatus.ACTIVE or 
                                 p.get_hand_status() == PlayerHandStatus.ALL_IN]

        if len(active_players_in_round) <= 1: 
            if len(active_players_in_round) == 1 and active_players_in_round[0].get_hand_status() == PlayerHandStatus.FOLDED:
                # זה לא אמור לקרות אם השחקנים הפעילים הוגדרו נכון.
                self._status = BettingRoundStatus.COMPLETED # סבב הסתיים, שחקן בודד נותר זוכה.
            else:
                self._status = BettingRoundStatus.NO_ACTIVE_PLAYERS # נותר רק שחקן אחד או פחות
            print(f"סבב הימורים הסתיים: {self._status.value}")
            return

        # בדיקה האם כולם השוו או הלכו אול-אין
        all_players_matched_or_all_in = True
        for player in active_players_in_round:
            # שחקן פעיל חייב להשוות את ההימור המקסימלי
            if player.get_hand_status() == PlayerHandStatus.ACTIVE and \
               player.get_current_bet() < self._current_max_bet_in_round:
                all_players_matched_or_all_in = False
                break
        
        # אם כולם השוו או אול-אין, והתור חזר לנקודת ההתחלה של הסבב/רייז האחרון
        if all_players_matched_or_all_in and \
           (self._current_player_index >= len(self._active_players) or self._active_players[self._current_player_index].get_user_id() == self._round_starter_id):
            self._status = BettingRoundStatus.COMPLETED
            print(f"סבב הימורים הסתיים: כולם השוו או אול-אין, והתור חזר לנקודת ההתחלה. סטטוס: {self._status.value}")
        else:
            # אם לא הסתיים, הוא עדיין ב-IN_PROGRESS
            print(f"סבב הימורים עדיין פעיל. שחקן בתור: {self.get_current_player().get_username()}")


    def end_round_and_collect_bets(self):
        """
        מסיים את הסבב, אוסף את כל ההימורים של הסבב הנוכחי לקופה,
        ומאפס את הימורי הסבב של השחקנים.
        נקרא בסיום כל סבב הימורים (לפני פתיחת קלפים חדשים, או בסיום היד).
        """
        # ודא שהסבב הסתיים לפני איסוף ההימורים
        if self._status == BettingRoundStatus.IN_PROGRESS:
            print("אזהרה: מנסה לסיים סבב הימורים שעדיין פעיל. מאלץ סיום.")
            # במצב אמיתי, נזרוק שגיאה או נחכה שיסתיים.
            # עבור המקרה הזה, אם הגענו לכאן בטעות כשהוא IN_PROGRESS, נסיים אותו.
            self._check_round_completion() # וודא שזה יעבור ל-COMPLETED או NO_ACTIVE_PLAYERS

        print("אוסף הימורים מהסבב הנוכחי לתוך הקופה הראשית.")
        
        # שלב 1: איסוף הימורים בפועל
        all_players_total_bets_in_hand = {p.get_user_id(): p.get_current_bet() for p in self._active_players}
        self._pot.collect_round_bets(self._player_round_bets, all_players_total_bets_in_hand)

        # שלב 2: איפוס הימורים בסבב של השחקנים
        for player in self._active_players:
            self._player_round_bets[player.get_user_id()] = 0 # מאפס את מה שהם שמו בסבב זה

        print(f"סך הקופה כעת: {self._pot.get_total_pot_size()}")


    def get_status(self) -> BettingRoundStatus:
        """מחזירה את הסטטוס הנוכחי של סבב ההימורים."""
        return self._status

    def __str__(self) -> str:
        return (
            f"Betting Round Status: {self._status.value}\n"
            f"Current Max Bet: {self._current_max_bet_in_round}\n"
            f"Current Player To Act: {self.get_current_player().get_username() if self.get_current_player() else 'None'}\n"
            f"Active Players: {[p.get_username() for p in self._active_players]}"
        )

    def __repr__(self) -> str:
        return (
            f"BettingRound(status={self._status.value}, "
            f"max_bet={self._current_max_bet_in_round}, "
            f"current_player_index={self._current_player_index})"
        )