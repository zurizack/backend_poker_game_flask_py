# poker_server/game/engine/player_oop.py

import logging
import enum
from typing import List, Optional, Dict, Any

# Import existing classes
from .card_oop import Card
from ...models.user import User as ActualUser 

# Import new/updated classes
from .player_hand import PlayerHand, PlayerHandStatus, PlayerAction
from .chip_stack import Chips 

logger = logging.getLogger(__name__)

class Player:
    """
    A class representing a specific player. This player can be connected,
    viewing multiple tables, and/or seated at multiple tables simultaneously.
    Each seated position will have its own chip stack and hand state.
    """

    def __init__(self, 
                 user: ActualUser, 
                 socket_id: Optional[str] = None):
        """
        Constructor for the Player class.
        Initializes a Player object as a connected user, not seated at any table.

        :param user: An object of your actual User model from your authentication system.
        :param socket_id: The unique socket ID of the player's current connection.
        """
        
        self._user: ActualUser = user  # Reference to your general User object (for total chips)
        self._user_id: int = user.id 
        self._username: str = user.nickname 
        self._socket_id: Optional[str] = socket_id
        
        # ✅ שינוי ארכיטקטוני: מילון לניהול מיקומי ישיבה פעילים
        # Key: table_id (str), Value: Dict[str, Any] containing {'seat_number': int, 'chips_on_table': Chips, 'player_hand': PlayerHand}
        self._seated_positions: Dict[str, Dict[str, Any]] = {} 
        
        # ✅ שינוי ארכיטקטוני: סט של table_ids שהשחקן צופה בהם
        self._viewing_tables: set[str] = set()

        logger.debug(f"Player {self._username} (ID: {self._user_id}) initialized as a connected user (not seated at any table).")

    # --- Properties and Setters for core attributes ---
    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @property
    def socket_id(self) -> Optional[str]:
        return self._socket_id

    @socket_id.setter
    def socket_id(self, value: str):
        self._socket_id = value
        logger.debug(f"Socket ID for player {self._username} (ID: {self._user_id}) updated to {value}.")

    # --- Methods for general User information (bank account) ---
    def get_user_total_chips(self) -> float: # Assuming user.chips is float
        """Returns the total chips in the user's general account (off the table)."""
        return self._user.chips

    # --- Methods for managing seated positions and chips on specific tables ---

    def is_seated_at_table(self, table_id: str) -> bool:
        """Checks if the player is seated at a specific table."""
        return table_id in self._seated_positions

    # def is_seated_at_any_table(self) -> bool: # ✅ פונקציה חדשה
    #     """
    #     Checks if the player is currently seated at any table.
    #     """
    #     return bool(self._seated_tables_data)

    def get_seated_position(self, table_id: str) -> Optional[Dict[str, Any]]:
        """Returns the seated position data for a specific table."""
        return self._seated_positions.get(table_id)

    def get_all_seated_tables(self) -> List[str]:
        """Returns a list of table IDs where the player is currently seated."""
        return list(self._seated_positions.keys())

    def get_chips_on_table(self, table_id: str) -> float:
        """Returns the amount of chips the player has on a specific table."""
        seated_data = self._seated_positions.get(table_id)
        if seated_data and 'chips_on_table' in seated_data:
            return seated_data['chips_on_table'].get_amount()
        return 0.0 # Return 0 if not seated at this table or no chips

    def get_seat_number(self, table_id: str) -> Optional[int]:
        """Returns the seat number for a specific table."""
        seated_data = self._seated_positions.get(table_id)
        if seated_data and 'seat_number' in seated_data:
            return seated_data['seat_number']
        return None

    def perform_buy_in(self, table_id: str, amount: float):
        """
        Performs a buy-in for a specific table: transfers chips from the player's
        general account to their stack on that table.
        This method should only be called if the player is about to be seated or is already seated.
        """
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Buy-in amount must be a positive number.")
        
        if self._user.chips < amount: 
            raise ValueError(f"User {self._username} (ID: {self._user_id}) does not have enough chips in their account ({self._user.chips}) to buy in {amount} chips.")
        
        # If not yet seated at this table, initialize the chips and hand objects
        if table_id not in self._seated_positions:
            self._seated_positions[table_id] = {
                'chips_on_table': Chips(initial_amount=0.0),
                'player_hand': PlayerHand(),
                'seat_number': None # Seat number will be set by set_seated_data_for_table
            }
            logger.debug(f"Initialized new seated position data for player {self._username} at table {table_id}.")
        
        table_chips = self._seated_positions[table_id]['chips_on_table']
        table_chips.add(amount) # Add chips to the player's table stack
        self._user.chips -= amount # Deduct chips from the general account
        logger.info(f"Player {self._username} (ID: {self._user_id}) performed buy-in of {amount} chips for table {table_id}. Total table chips: {table_chips.get_amount()}. User's total chips: {self._user.chips}.")

    def add_chips_to_table(self, table_id: str, amount: float):
        """Adds chips to the player's chip stack on a specific table (e.g., winning a pot)."""
        if not self.is_seated_at_table(table_id):
            logger.warning(f"Cannot add chips to player {self._username} at table {table_id}: not seated.")
            return
        self._seated_positions[table_id]['chips_on_table'].add(amount)
        logger.debug(f"Player {self._username} added {amount} chips to table {table_id}. Total: {self.get_chips_on_table(table_id)}.")

    def remove_chips_from_table(self, table_id: str, amount: float):
        """Removes chips from the player's chip stack on a specific table (e.g., losing a bet)."""
        if not self.is_seated_at_table(table_id):
            logger.warning(f"Cannot remove chips from player {self._username} at table {table_id}: not seated.")
            return
        self._seated_positions[table_id]['chips_on_table'].remove(amount)
        logger.debug(f"Player {self._username} removed {amount} chips from table {table_id}. Total: {self.get_chips_on_table(table_id)}.")

    def can_afford(self, table_id: str, amount: float) -> bool:
        """Checks if the player has enough chips on a specific table."""
        if not self.is_seated_at_table(table_id):
            return False
        return self._seated_positions[table_id]['chips_on_table'].can_afford(amount)

    def return_chips_to_balance(self, table_id: str):
        """Returns all chips from a specific table stack to the user's general account."""
        if not self.is_seated_at_table(table_id):
            logger.warning(f"Player {self._username} (ID: {self._user_id}) tried to return chips from table {table_id} but was not seated there.")
            return
        
        remaining_chips = self._seated_positions[table_id]['chips_on_table'].get_amount()
        if remaining_chips > 0:
            self._user.chips += remaining_chips
            self._seated_positions[table_id]['chips_on_table'].remove(remaining_chips) # Clear table stack
            logger.info(f"Player {self._username} (ID: {self._user_id}) returned {remaining_chips} chips from table {table_id} to balance. New balance: {self._user.chips}.")
        else:
            logger.info(f"Player {self._username} (ID: {self._user_id}) had no chips to return from table {table_id}.")

    # --- Methods for managing seated status at a specific table ---

    def set_seated_data_for_table(self, table_id: str, seat_number: int):
        """
        Sets the seated data for a specific table.
        Assumes perform_buy_in has already been called if chips are needed.
        """
        if not isinstance(seat_number, int) or seat_number < 0:
            raise ValueError("Seat number must be a non-negative integer.")
        
        # Ensure the table entry exists (it should if perform_buy_in was called)
        if table_id not in self._seated_positions:
            self._seated_positions[table_id] = {
                'chips_on_table': Chips(initial_amount=0.0),
                'player_hand': PlayerHand()
            }
        
        self._seated_positions[table_id]['seat_number'] = seat_number
        self._seated_positions[table_id]['player_hand'].set_status(PlayerHandStatus.WAITING_FOR_NEW_HAND)
        logger.info(f"Player {self._username} (ID: {self._user_id}) is now seated at seat {seat_number} on table {table_id}.")

    def leave_table_position(self, table_id: str):
        """
        Removes player from a specific seated position, returns chips to balance.
        """
        if not self.is_seated_at_table(table_id):
            logger.warning(f"Player {self._username} (ID: {self._user_id}) tried to leave table {table_id} but was not seated there.")
            return
        
        self.return_chips_to_balance(table_id) # Return chips to general balance
        
        # Remove the seated position entry
        del self._seated_positions[table_id]
        logger.info(f"Player {self._username} (ID: {self._user_id}) has left their seat at table {table_id}.")

    # --- Methods for managing viewing tables ---

    def is_viewing_table(self, table_id: str) -> bool:
        """Checks if the player is currently viewing a specific table."""
        return table_id in self._viewing_tables

    def add_viewing_table(self, table_id: str):
        """Adds a table to the list of tables the player is viewing."""
        self._viewing_tables.add(table_id)
        logger.info(f"Player {self._username} (ID: {self._user_id}) is now viewing table {table_id}.")

    def remove_viewing_table(self, table_id: str):
        """Removes a table from the list of tables the player is viewing."""
        if table_id in self._viewing_tables:
            self._viewing_tables.remove(table_id)
            logger.info(f"Player {self._username} (ID: {self._user_id}) stopped viewing table {table_id}.")
        else:
            logger.warning(f"Player {self._username} (ID: {self._user_id}) tried to stop viewing table {table_id} but was not viewing it.")

    def get_all_viewing_tables(self) -> List[str]:
        """Returns a list of table IDs the player is currently viewing."""
        return list(self._viewing_tables)

    # --- Methods for managing hand state and game actions (delegates to PlayerHand per table) ---
    def get_hand(self, table_id: str) -> List[Card]:
        """Returns a copy of the player's hole cards for a specific table."""
        seated_data = self._seated_positions.get(table_id)
        if seated_data and 'player_hand' in seated_data:
            return seated_data['player_hand'].get_cards()
        return []

    def set_hand(self, table_id: str, cards: List[Card]):
        """Sets the player's hole cards for a specific table."""
        if not self.is_seated_at_table(table_id):
            logger.warning(f"Cannot set hand for unseated player {self._username} at table {table_id}.")
            return
        self._seated_positions[table_id]['player_hand'].set_cards(cards)

    def clear_hand(self, table_id: str):
        """Clears the player's hand cards for a specific table."""
        if not self.is_seated_at_table(table_id):
            logger.warning(f"Cannot clear hand for unseated player {self._username} at table {table_id}.")
            return
        self._seated_positions[table_id]['player_hand'].clear_cards()

    def get_current_bet(self, table_id: str) -> float:
        """Returns the player's total bet amount in the current hand for a specific table."""
        seated_data = self._seated_positions.get(table_id)
        if seated_data and 'player_hand' in seated_data:
            return seated_data['player_hand'].get_bet_in_hand()
        return 0.0

    def add_to_current_bet(self, table_id: str, amount: float):
        """Adds an amount to the player's cumulative bet in this hand for a specific table."""
        if not self.is_seated_at_table(table_id):
            logger.warning(f"Cannot add to bet for unseated player {self._username} at table {table_id}.")
            return
        self._seated_positions[table_id]['player_hand'].add_to_bet(amount)

    def reset_current_bet(self, table_id: str):
        """Resets the player's cumulative bet amount in this hand for a specific table."""
        if not self.is_seated_at_table(table_id):
            logger.warning(f"Cannot reset bet for unseated player {self._username} at table {table_id}.")
            return
        self._seated_positions[table_id]['player_hand'].reset_bet()

    def get_hand_status(self, table_id: str) -> PlayerHandStatus:
        """Returns the player's current hand status for a specific table."""
        seated_data = self._seated_positions.get(table_id)
        if seated_data and 'player_hand' in seated_data:
            return seated_data['player_hand'].get_status()
        return PlayerHandStatus.NOT_SEATED # Default status if not seated at this table

    def set_hand_status(self, table_id: str, status: PlayerHandStatus):
        """Sets the player's current hand status for a specific table."""
        if not self.is_seated_at_table(table_id):
            logger.warning(f"Cannot set hand status for unseated player {self._username} at table {table_id}.")
            return
        self._seated_positions[table_id]['player_hand'].set_status(status)

    def get_last_action(self, table_id: str) -> Optional[PlayerAction]:
        """Returns the last action performed by the player for a specific table."""
        seated_data = self._seated_positions.get(table_id)
        if seated_data and 'player_hand' in seated_data:
            return seated_data['player_hand'].get_last_action()
        return None

    def set_last_action(self, table_id: str, action: PlayerAction):
        """Sets the last action performed by the player for a specific table."""
        if not self.is_seated_at_table(table_id):
            logger.warning(f"Cannot set last action for unseated player {self._username} at table {table_id}.")
            return
        self._seated_positions[table_id]['player_hand'].set_last_action(action)

    def fold(self, table_id: str):
        """Performs a "fold" action for a specific table."""
        if not self.is_seated_at_table(table_id):
            logger.warning(f"Unseated player {self._username} cannot fold at table {table_id}.")
            return
        self._seated_positions[table_id]['player_hand'].set_status(PlayerHandStatus.FOLDED)
        self._seated_positions[table_id]['player_hand'].set_last_action(PlayerAction.FOLD)
        logger.info(f"Player {self._username} (ID: {self._user_id}) folded at table {table_id}.")

    def go_all_in(self, table_id: str):
        """Performs an "all-in" action for a specific table."""
        if not self.is_seated_at_table(table_id):
            raise ValueError(f"Unseated player {self._username} cannot go All-In at table {table_id}.")
        
        table_chips_obj = self._seated_positions[table_id]['chips_on_table']
        if table_chips_obj.get_amount() == 0: 
            raise ValueError("Cannot go all-in when there are no chips on the table.")
        
        amount_to_add = table_chips_obj.get_amount() 
        self._seated_positions[table_id]['player_hand'].add_to_bet(amount_to_add)
        table_chips_obj.remove(amount_to_add) # Chips moved from table stack to bet
        
        self._seated_positions[table_id]['player_hand'].set_status(PlayerHandStatus.ALL_IN)
        self._seated_positions[table_id]['player_hand'].set_last_action(PlayerAction.ALL_IN)
        logger.info(f"Player {self._username} (ID: {self._user_id}) went All-In with {amount_to_add} chips at table {table_id}.")

    def reset_hand_state(self, table_id: str):
        """Resets all hand-specific states for a new hand for a specific table."""
        if not self.is_seated_at_table(table_id):
            logger.warning(f"Cannot reset hand state for unseated player {self._username} at table {table_id}.")
            return
        self._seated_positions[table_id]['player_hand'].reset_state()
        self._seated_positions[table_id]['player_hand'].set_status(PlayerHandStatus.WAITING_FOR_NEW_HAND)
        logger.debug(f"Player {self._username} (ID: {self._user_id}) hand state reset for table {table_id}.")

    # --- Display and Debugging Methods ---
    def __str__(self) -> str:
        """
        Returns a readable representation of the player, for display purposes.
        Shows general info and then details for each table they are seated at or viewing.
        """
        base_str = f"Player: {self.username} (ID: {self.user_id})"
        
        seated_str = ""
        if self._seated_positions:
            seated_details = []
            for table_id, data in self._seated_positions.items():
                status_en = { # Changed to English status mapping
                    PlayerHandStatus.ACTIVE: "Active",
                    PlayerHandStatus.FOLDED: "Folded",
                    PlayerHandStatus.ALL_IN: "All-In",
                    PlayerHandStatus.WAITING_FOR_NEW_HAND: "Waiting for new hand",
                    PlayerHandStatus.NOT_SEATED: "Not Seated", 
                    PlayerHandStatus.SITTING_OUT: "Sitting Out"
                }
                status_display = status_en.get(data['player_hand'].get_status(), "Unknown") 
                last_action_display = data['player_hand'].get_last_action().value if data['player_hand'].get_last_action() else "None"
                seated_details.append(
                    f"  - Table {table_id} (Seat {data['seat_number']}): "
                    f"Chips: {data['chips_on_table'].get_amount()}, "
                    f"Bet: {data['player_hand'].get_bet_in_hand()}, "
                    f"Status: {status_display}, Action: {last_action_display}"
                )
            seated_str = "\nSeated at:\n" + "\n".join(seated_details)

        viewing_str = ""
        if self._viewing_tables:
            viewing_str = f"\nViewing tables: {', '.join(self._viewing_tables)}"

        return base_str + seated_str + viewing_str

    def __repr__(self) -> str:
        """
        Returns an unambiguous representation of the object, used for debugging and development.
        """
        return (
            f"Player(user_id={self.user_id}, username='{self.username}', "
            f"socket_id='{self.socket_id}', "
            f"seated_positions={repr(self._seated_positions)}, "
            f"viewing_tables={repr(self._viewing_tables)})"
        )

    # --- Method to convert Player object to a dictionary for JSON purposes ---
    def to_dict(self, include_private_data: bool = False, table_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Converts the Player object to a dictionary suitable for JSON conversion.
        :param include_private_data: Whether to include private data such as cards in hand (for the player themselves).
        :param table_id: If provided, returns data specific to this table (e.g., chips, seat, hand status).
        """
        player_data = {
            'id': self.user_id, 
            'username': self.username, 
            'is_connected': self.socket_id is not None,
            'total_account_chips': self.get_user_total_chips(), # General account chips
            'seated_tables': self.get_all_seated_tables(), # List of tables where player is seated
            'viewing_tables': self.get_all_viewing_tables(), # List of tables player is viewing
        }

        if table_id and self.is_seated_at_table(table_id):
            seated_info = self._seated_positions[table_id]
            player_data['chips_on_current_table'] = seated_info['chips_on_table'].get_amount()
            player_data['seat_number_on_current_table'] = seated_info['seat_number']
            player_data['current_bet_on_current_table'] = seated_info['player_hand'].get_bet_in_hand()
            player_data['last_action_on_current_table'] = seated_info['player_hand'].get_last_action().value if seated_info['player_hand'].get_last_action() else None
            player_data['hand_status_on_current_table'] = seated_info['player_hand'].get_status().value
            
            if include_private_data:
                player_data['hand_on_current_table'] = [card.to_dict() for card in seated_info['player_hand'].get_cards()]
            else:
                player_data['cards_count_on_current_table'] = len(seated_info['player_hand'].get_cards())
        elif table_id and self.is_viewing_table(table_id):
            player_data['is_viewing_current_table'] = True
            player_data['chips_on_current_table'] = 0.0 # Viewers have 0 chips on table
            player_data['seat_number_on_current_table'] = None
            player_data['current_bet_on_current_table'] = 0.0
            player_data['last_action_on_current_table'] = None
            player_data['hand_status_on_current_table'] = PlayerHandStatus.NOT_SEATED.value
            player_data['cards_count_on_current_table'] = 0
        else:
            # If no specific table_id requested or not seated/viewing there
            player_data['chips_on_current_table'] = 0.0
            player_data['seat_number_on_current_table'] = None
            player_data['current_bet_on_current_table'] = 0.0
            player_data['last_action_on_current_table'] = None
            player_data['hand_status_on_current_table'] = PlayerHandStatus.NOT_SEATED.value
            player_data['cards_count_on_current_table'] = 0

        return player_data
