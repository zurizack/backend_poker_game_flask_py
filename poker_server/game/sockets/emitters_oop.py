import logging
from typing import Dict, Any, Optional, List
from flask_socketio import SocketIO, join_room
# מייבאים את SocketIO כדי להשתמש בו כ-type hint
# ייבוא של המחלקות שאתה עובד איתן
# חשוב: ודא שהנתיבים האלה נכונים.
# אם הקובץ Table והקובץ Player נמצאים בתיקיות game.engine, זה תקין.
from backend.poker_server.game.engine.table_oop import Table
from backend.poker_server.game.engine.player_oop import Player
from backend.poker_server.game.engine.card_oop import Card # נצטרך את זה אם נשלח קלפים

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # לוגים ברמת מידע
# ניתן לשנות ל-DEBUG עבור פיתוח מפורט יותר: logger.setLevel(logging.DEBUG)


class PokerEmitters:
    """
    מחלקה שמכילה את כל פונקציות השידור (emit) של השרת.
    מאותחלת עם מופע ה-SocketIO הראשי.
    """
    _socketio_instance: Optional[SocketIO] = None

    @classmethod
    def initialize(cls, socketio_ref: SocketIO):
        """
        מאותחל את מחלקת ה-Emitters עם מופע ה-SocketIO הראשי.
        נקרא פעם אחת ב-app.py בעת אתחול השרת.
        """
        cls._socketio_instance = socketio_ref
        logger.info("PokerEmitters initialized with SocketIO instance.")

    @classmethod
    def _emit(cls, event_name: str, data: Dict[str, Any], room: Optional[str] = None, sid: Optional[str] = None):
        """
        פונקציית עזר פנימית לביצוע השידור בפועל.
        היא מקבלת room או sid, ומשדרת בהתאם.
        """
        if not cls._socketio_instance:
            logger.error(f"Emitters: SocketIO instance not initialized. Cannot emit event '{event_name}'.")
            return

        if room:
            cls._socketio_instance.emit(event_name, data, room=room)
            logger.debug(f"Emitters: Emitted '{event_name}' to room '{room}' with data: {data}")
        elif sid:
            cls._socketio_instance.emit(event_name, data, to=sid) # שימוש ב-to=sid עדיף על room=sid ללקוח בודד
            logger.debug(f"Emitters: Emitted '{event_name}' to SID '{sid}' with data: {data}")
        else:
            # אם אין חדר או SID, נניח שזה שידור כללי לכל החיבורים (פחות נפוץ במשחקים ספציפיים לשולחן)
            cls._socketio_instance.emit(event_name, data)
            logger.debug(f"Emitters: Emitted '{event_name}' globally with data: {data}")

    # --- פונקציות פליטה כלליות ---

    @classmethod
    def emit_error(cls, sid: str, message: str):
        """
        משדר הודעת שגיאה לקליינט ספציפי.
        אירוע: 'error'
        נתונים: {"message": "..."}
        """
        logger.warning(f"Emitting error to SID {sid}: {message}")
        cls._emit('error', {"message": message}, sid=sid)

    @classmethod
    def emit_join_success(cls, sid: str, table_id: str, role: str, message: str):
        """
        משדר הודעת הצלחה על הצטרפות לשולחן לקליינט ספציפי.
        אירוע: 'join_success'
        נתונים: {"table_id": "...", "role": "...", "message": "..."}
        """
        logger.info(f"Emitting join_success to SID {sid} for table {table_id} as {role}.")
        cls._emit('join_success', {'table_id': table_id, 'role': role, 'message': message}, sid=sid)
        
        # חשוב: כאן מוסיפים את ה-SID לחדר של השולחן!
        # ה-SID צריך להצטרף לחדר ספציפי לשולחן כדי שיוכל לקבל עדכונים לכל החדר.
        # SocketIO מספק את הפונקציה join_room
        if cls._socketio_instance and sid: # וודא ש-sid לא None לפני השימוש
            join_room(str(table_id), sid=sid) # room_name, sid
            logger.debug(f"SID {sid} הצטרף לחדר השולחן {table_id}.")

    def emit_player_seated_success(cls, sid: str, table_id: str, seat_number: int, message: str):
        logger.info(f"Emitting seat_success to SID {sid} for table {table_id} and sit {seat_number}.")
        cls._emit('seat_success', {'table_id': table_id, 'seat_number': seat_number, 'message': message}, sid=sid)
        if cls._socketio_instance and sid: # וודא ש-sid לא None לפני השימוש
            join_room(str(table_id), sid=sid) # room_name, sid
            logger.debug(f"SID {sid} הצטרף לחדר השולחן {table_id}.")
            
    # --- פונקציות פליטה למצב שולחן מלא ---

    @classmethod
    def emit_full_table_state(cls, target_sid: str, table_obj: Table, requesting_player_id: Optional[str] = None):
        """
        שולחת את כל מצב השולחן ללקוח ספציפי.
        נתונים ספציפיים לשחקן (כמו קלפי יד) מותאמים ללקוח המבקש.
        אירוע: 'full_table_state'
        נתונים: מילון של כל מצב השולחן.
        """
        logger.info(f"Emitting full_table_state to SID: {target_sid}. Requesting player: {requesting_player_id}")
        
        # יצירת מילון מצב השולחן
        # ההנחה היא של-table_obj יש מתודת to_dict שמקבלת requesting_player_id
        # וחושפת קלפים פרטיים רק לשחקן המבקש.
        table_state_data = table_obj.to_dict(requesting_player_id=requesting_player_id)
        
        cls._emit('full_table_state', table_state_data, sid=target_sid)
        logger.debug(f"Full table state emitted to SID {target_sid}.")

    @classmethod
    def emit_full_table_state_to_room(cls, table_id: str, table_obj: Table):
        """
        שולחת את מצב המשחק הציבורי המלא (ללא קלפי יד פרטיים) לכל הקליינטים בחדר השולחן.
        מתאים לצופים או לאתחול מצב כללי.
        אירוע: 'full_table_state_public'
        נתונים: מילון של מצב השולחן (ציבורי).
        """
        logger.info(f"Emitting full_table_state_public to room: {table_id}.")
        public_table_state = table_obj.to_dict(requesting_player_id=None) # חשוב: אין ID שחקן מבקש
        cls._emit('full_table_state_public', public_table_state, room=str(table_id))
        logger.debug(f"Full public table state emitted to room {table_id}.")

    # --- פונקציות פליטה לעדכונים חלקיים (אירועים ספציפיים) ---

    @classmethod
    def emit_player_seated(cls, table_id: str, player_info: Dict[str, Any]):
        """
        משדר כאשר שחקן התיישב בשולחן.
        אירוע: 'player_seated'
        נתונים: {"player_id": "...", "username": "...", "seat_number": ..., "chips": ...}
        """
        logger.info(f"Emitting player_seated for table {table_id}: {player_info['username']} at seat {player_info['seat_number']}.")
        cls._emit('player_seated', player_info, room=str(table_id))

    @classmethod
    def emit_player_left(cls, table_id: str, player_id: str, seat_number: int):
        """
        משדר כאשר שחקן עזב את השולחן.
        אירוע: 'player_left'
        נתונים: {"player_id": "...", "seat_number": ...}
        """
        logger.info(f"Emitting player_left for table {table_id}: player {player_id} from seat {seat_number}.")
        cls._emit('player_left', {"player_id": player_id, "seat_number": seat_number}, room=str(table_id))

    @classmethod
    def emit_hand_started(cls, table_id: str, hand_number: int, dealer_seat: int, small_blind_amount: int, big_blind_amount: int):
        """
        משדר כאשר יד פוקר חדשה מתחילה.
        אירוע: 'hand_started'
        נתונים: {"hand_number": ..., "dealer_seat": ..., "small_blind_amount": ..., "big_blind_amount": ...}
        """
        logger.info(f"Emitting hand_started for table {table_id}: Hand #{hand_number}, Dealer: {dealer_seat}.")
        cls._emit('hand_started', {
            "hand_number": hand_number,
            "dealer_seat": dealer_seat,
            "small_blind_amount": small_blind_amount,
            "big_blind_amount": big_blind_amount
        }, room=str(table_id))

    @classmethod
    def emit_player_cards_dealt(cls, sid: str, hand_cards: List[Dict[str, Any]]):
        """
        משדר את קלפי היד הספציפיים לשחקן.
        אירוע: 'your_cards'
        נתונים: {"cards": [{"rank": "...", "suit": "..."}, ...]}
        """
        logger.info(f"Emitting player_cards_dealt to SID {sid}.")
        # hand_cards צפוי להיות רשימה של מילונים המייצגים קלפים, לדוגמה:
        # [{"rank": card.rank.value, "suit": card.suit.value} for card in player_hand_cards]
        cls._emit('your_cards', {"cards": hand_cards}, sid=sid)
        
    @classmethod
    def emit_player_acted(
        cls,
        table_id: str,
        player_id: str,
        action_type: str, # 'fold', 'check', 'call', 'bet', 'raise'
        amount: int,      # הסכום שהשחקן שם (עבור call/bet/raise)
        current_bet_in_round: int, # הסכום הכולל שהשחקן הימר בסבב הנוכחי
        player_chips_on_table: int, # יתרת הצ'יפים של השחקן על השולחן
        pot_size: int, # גודל הקופה הכולל לאחר הפעולה
        next_player_to_act_seat: Optional[int] = None, # הכיסא של השחקן הבא לפעול (אם ידוע)
        next_player_call_amount: Optional[int] = None # הסכום שצריך להשוות עבור השחקן הבא (אם ידוע)
    ):
        """
        משדר עדכון על פעולת שחקן לכל הקליינטים בחדר השולחן.
        זהו אירוע מפורט יותר המשלב את 'player_action_update' מהקוד המקורי.
        אירוע: 'player_acted'
        נתונים: {"player_id": "...", "action_type": "...", "amount": ..., "current_bet_in_round": ...,
                 "player_chips_on_table": ..., "pot_size": ..., "next_player_to_act_seat": ...,
                 "next_player_call_amount": ...}
        """
        action_data = {
            "player_id": player_id,
            "action_type": action_type,
            "amount": amount,
            "current_bet_in_round": current_bet_in_round,
            "player_chips_on_table": player_chips_on_table,
            "pot_size": pot_size,
            "next_player_to_act_seat": next_player_to_act_seat,
            "next_player_call_amount": next_player_call_amount
        }
        logger.info(f"Emitting player_acted for table {table_id}: {player_id} {action_type} {amount}.")
        cls._emit('player_acted', action_data, room=str(table_id))

    @classmethod
    def emit_community_cards_updated(cls, table_id: str, new_cards: List[Dict[str, Any]], phase: str):
        """
        משדר כאשר קלפי קהילה חדשים נפתחו (Flop, Turn, River).
        אירוע: 'community_cards_updated'
        נתונים: {"cards": [{"rank": "...", "suit": "..."}, ...], "phase": "flop"|"turn"|"river"}
        """
        logger.info(f"Emitting community_cards_updated for table {table_id} (phase: {phase}). Cards: {new_cards}")
        cls._emit('community_cards_updated', {"cards": new_cards, "phase": phase}, room=str(table_id))

    @classmethod
    def emit_pot_size_update(cls, table_id: str, new_pot_size: int):
        """
        משדר עדכון על גודל הקופה.
        ניתן לקרוא לזה אחרי איסוף בליינדים או אחרי סבב הימורים.
        אירוע: 'pot_size_update'
        נתונים: {"pot_size": ...}
        """
        logger.info(f"Emitting pot_size_update for table {table_id}. New size: {new_pot_size}.")
        cls._emit('pot_size_update', {"pot_size": new_pot_size}, room=str(table_id))

    @classmethod
    def emit_betting_round_started(cls, table_id: str, round_name: str, current_player_seat: int, call_amount: int):
        """
        משדר כאשר סבב הימורים חדש מתחיל.
        אירוע: 'betting_round_started'
        נתונים: {"round_name": "...", "current_player_seat": ..., "call_amount": ...}
        """
        logger.info(f"Emitting betting_round_started for table {table_id}: {round_name}, First to act: {current_player_seat}.")
        cls._emit('betting_round_started', {
            "round_name": round_name,
            "current_player_seat": current_player_seat,
            "call_amount": call_amount
        }, room=str(table_id))
        
    @classmethod
    def emit_betting_round_ended(cls, table_id: str, final_pot_size_for_round: int):
        """
        משדר כאשר סבב הימורים הסתיים.
        אירוע: 'betting_round_ended'
        נתונים: {"final_pot_size": ...}
        """
        logger.info(f"Emitting betting_round_ended for table {table_id}. Pot collected: {final_pot_size_for_round}.")
        cls._emit('betting_round_ended', {"final_pot_size": final_pot_size_for_round}, room=str(table_id))

    @classmethod
    def emit_hand_ended(cls, table_id: str, winners_info: List[Dict[str, Any]], pot_breakdown: List[Dict[str, Any]]):
        """
        משדר כאשר יד מסתיימת, עם פרטי הזוכים וחלוקת הקופה.
        אירוע: 'hand_ended'
        נתונים: {"winners": [...], "pot_breakdown": [...]}
        winners_info: [{"player_id": "...", "username": "...", "seat_number": ..., "winnings": ..., "hand_rank": "...", "best_five_cards": [...]}, ...]
        pot_breakdown: [{"pot_type": "main"|"side", "amount": ..., "winners": [...]}, ...]
        """
        logger.info(f"Emitting hand_ended for table {table_id}. Winners: {winners_info}.")
        cls._emit('hand_ended', {
            "winners": winners_info,
            "pot_breakdown": pot_breakdown # זה ידרוש לוגיקה במחלקת Pot
        }, room=str(table_id))

    @classmethod
    def emit_game_over(cls, table_id: str, message: str):
        """
        משדר כאשר המשחק בשולחן מסתיים (לדוגמה, אין מספיק שחקנים עם צ'יפים).
        אירוע: 'game_over'
        נתונים: {"message": "..."}
        """
        logger.info(f"Emitting game_over for table {table_id}: {message}.")
        cls._emit('game_over', {"message": message}, room=str(table_id))