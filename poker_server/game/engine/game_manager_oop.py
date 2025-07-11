# poker_server/game/engine/game_manager_oop.py

import logging
from typing import Dict, Any, Optional, List

# Ensure these imports exist:
from poker_server.models.user import User # Ensure this is your correct User model
from poker_server.game.engine.player_oop import Player # Ensure this is the updated Player file
from poker_server.game.engine.table_oop import Table
from poker_server.sql_services.db_manager import DBManager
from poker_server.game.engine.hand_evaluator_oop import HandEvaluator 


logger = logging.getLogger(__name__)

class GameManager:
    def __init__(self, db_manager: DBManager):
        self._db_manager: DBManager = db_manager 
        self._tables: Dict[str, Table] = {} 
        self._connected_players: Dict[int, Player] = {} # user_id -> Player object
        self.logger = logging.getLogger(__name__)
        self._hand_evaluator = HandEvaluator()
        self.logger.info("HandEvaluator initialized successfully.")
        self._load_existing_tables()
        self.logger.info("GameManager initialized successfully.")
        self.logger.info(f"GameManager: DBManager initialized successfully.") 

    def _load_existing_tables(self):
        poker_tables_data = self._db_manager.get_all_poker_tables() 
        self.logger.info(f"Retrieved {len(poker_tables_data)} poker tables from the database.")

        if poker_tables_data:
            self.logger.info(f"Loading {len(poker_tables_data)} existing tables from the database...")
            for table_data in poker_tables_data:
                table_id = str(table_data['id'])
                table_name = table_data['name'] # Table name
                max_players = table_data['max_players']
                small_blind = table_data['small_blind']
                big_blind = table_data['big_blind']

                poker_table = Table(
                    table_id=table_id,
                    name=table_name, 
                    max_players=max_players,
                    small_blind=small_blind,
                    big_blind=big_blind,
                    hand_evaluator=self._hand_evaluator
                )
                self._tables[table_id] = poker_table
                print(f"Table '{table_name}' (ID: {table_id}) created.")
        else:
            self.logger.info("No existing poker tables found in the database.")

    def get_table_by_id(self, table_id: str) -> Optional[Table]:
        table = self._tables.get(table_id)
        if table:
            self.logger.debug(f"Table {table_id} found.")
        else:
            self.logger.warning(f"Table {table_id} not found.")
        return table

    def get_player_by_id(self, player_id: int) -> Optional[Player]:
        """Returns a Player object by its ID."""
        return self._connected_players.get(player_id)

    def get_player_by_user_id(self, user_id: int) -> Optional[Player]:
        """Returns a Player object by its user_id."""
        return self._connected_players.get(user_id)

    def get_player_id_by_socket_id(self, sid: str) -> Optional[int]:
        """
        Returns the user_id of a player by their socket_id.
        """
        for player_id, player_obj in self._connected_players.items():
            if player_obj.socket_id == sid:
                return player_id
        return None

    def update_player_socket_id(self, user_id: int, new_sid: str):
        """Updates the socket_id of an existing player."""
        player = self.get_player_by_user_id(user_id)
        if player:
            player.socket_id = new_sid
            self.logger.debug(f"Player {user_id} socket ID updated to {new_sid}.")
        else:
            self.logger.warning(f"Cannot update socket ID for non-existent player {user_id}.")

    def mark_player_reconnected(self, player_id: int):
        """Marks a player as reconnected (future logic for handling temporary disconnections)."""
        player = self.get_player_by_user_id(player_id)
        if player:
            self.logger.info(f"Player {player_id} marked as reconnected.")
        else:
            self.logger.warning(f"Cannot mark non-existent player {player_id} as reconnected.")

    def mark_player_disconnected(self, player_id: int):
        """Marks a player as disconnected (future logic for handling temporary disconnections and timers)."""
        player = self.get_player_by_user_id(player_id)
        if player:
            self.logger.info(f"Player {player_id} marked as disconnected.")
        else:
            self.logger.warning(f"Cannot mark non-existent player {player_id} as disconnected.")

    def add_player_to_table_as_viewer(self, player_id: int, table_id: str) -> bool:
        """
        Adds a player to a table as a viewer.
        :param player_id: The player's ID.
        :param table_id: The table's ID.
        :return: True if the viewer was successfully added, False otherwise.
        """
        player_obj = self.get_player_by_user_id(player_id)
        if not player_obj:
            self.logger.warning(f"Cannot add viewer: Player {player_id} not found in connected players.")
            return False

        table = self.get_table_by_id(table_id)
        if not table:
            self.logger.warning(f"Cannot add viewer: Table {table_id} not found.")
            return False
        
        # ✅ Check: If the player is already seated at this table, they cannot also be a viewer.
        if player_obj.is_seated_at_table(table_id):
            self.logger.warning(f"Player {player_obj.username} (ID: {player_id}) is already seated at table {table_id}. Cannot add as viewer to the same table.")
            return False

        # Call the method within the Table object
        success = table.add_viewer(player_obj) 
        if success:
            # ✅ Update the player's viewing status in the Player object
            player_obj.add_viewing_table(table_id) 
            self.logger.info(f"Player {player_id} added as viewer to table {table_id}.")
            return True
        else:
            self.logger.warning(f"Failed to add player {player_id} as viewer to table {table_id}.")
            return False

    def add_player_to_table_as_player(self, player_id: int, table_id: str, buy_in_amount: float, seat_number: int) -> bool:
        """
        Handles the logic for a player taking a seat at a table.
        - Ensures the player exists in the system (connected).
        - Ensures the table and seat exist and are available.
        - Ensures the player has enough chips for the buy-in.
        - Seats the player at the seat.
        - Updates the table state.
        """
        self.logger.info(f"Player {player_id} attempting to join table {table_id} at seat {seat_number} with buy-in {buy_in_amount}.")

        player_obj = self.get_player_by_id(player_id)
        if not player_obj:
            self.logger.warning(f"Failed to seat player: Player {player_id} not found in connected players.")
            return False

        table = self.get_table_by_id(table_id)
        if not table:
            self.logger.warning(f"Failed to seat player: Table {table_id} not found.")
            return False

        # ✅ No need to check here if the player is seated at another table.
        # The assumption is that player_obj can be seated at multiple tables.
        # The check if the seat at the current table is free will be done inside table.take_seat.
        # The check if the player is already seated at *the same table* will be done inside table.take_seat.


        # 1. Ensure the player has enough chips in their total account
        # (Note: player_obj.get_user_total_chips() returns the user's total balance from the DB)
        if player_obj.get_user_total_chips() < buy_in_amount: 
            self.logger.warning(f"Player {player_id} tried to buy in with {buy_in_amount} but only has {player_obj.get_user_total_chips()} chips in total.")
            return False 

        # 2. Try to seat the player at the table
        # ✅ The assumption is that table.take_seat handles:
        #    a. Checking if the seat is free.
        #    b. Checking if the player is already seated at this seat at this table (and preventing).
        #    c. Removing the player from table._viewers if they were a viewer at the same table.
        #    d. Calling player_obj.perform_buy_in(self.table_id, buy_in_amount)
        #    e. Calling player_obj.set_seated_data_for_table(self.table_id, seat_number)
        #    f. Adding the player to table._players and table._seats.
        success = table.take_seat(player_obj, seat_number, buy_in_amount)

        if success:
            # 3. Database update (reducing player chips) will be performed in the SocketIO handler
            #    (the handler will perform session.commit() on the modified User object).
            # ❌ This line was removed! It was causing the double update and chip reset issue.
            # self._db_manager.update_user_chips(player_id, player_obj.get_user_total_chips()) 

            self.logger.info(f"Player {player_id} successfully took seat {seat_number} on table {table_id} with {buy_in_amount} buy-in.")
            return True
        else:
            self.logger.warning(f"Failed to seat player {player_id} at table {table_id}, seat {seat_number}.")
            return False

    def get_table_state(self, table_id: str) -> Optional[Dict[str, Any]]:
        """
        Returns the full table state as a dictionary, ready for transmission to the client.
        :param table_id: The ID of the table.
        :return: A dictionary representing the table state, or None if the table is not found.
        """
        table = self.get_table_by_id(table_id)
        if table:
            return table.to_dict() 
        return None

    def register_or_update_player_connection(self, user: User, sid: str) -> Optional[Player]:
        player_id = user.id 
        player = self._connected_players.get(player_id)
        if player:
            if player.socket_id != sid:
                self.logger.info(f"Updating socket ID for player {player_id} from {player.socket_id} to {sid}.")
                player.socket_id = sid
            self.logger.info(f"Existing Player object retrieved for user_id {player_id}.")
        else:
            print(" see the user chips: ", user.chips)
            player = Player(user=user, socket_id=sid) 
            self._connected_players[player_id] = player
            self.logger.info(f"New Player object created for user_id <User {user.nickname}> (username: {user.nickname}).")
        return player
