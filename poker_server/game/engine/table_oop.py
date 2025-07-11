# poker_server/game/engine/table_oop.py

import logging
from typing import Dict, Any, List, Optional
# Ensure these imports exist:
from .player_oop import Player # Ensure this is the updated Player file
from .card_oop import Card 
from .hand_evaluator_oop import HandEvaluator 
from .pot import Pot # ✅ Correction: Changed to pot_oop
from .betting_round import BettingRound, BettingRoundStatus 
from .card_deck_oop import CardDeck # ✅ Correction: Changed to deck_oop
from .player_hand import PlayerHandStatus, PlayerAction 
import enum 

logger = logging.getLogger(__name__)

class TableStatus(enum.Enum):
    """
    Possible statuses for the table.
    """
    WAITING_FOR_PLAYERS = "waiting_for_players"
    READY_TO_START = "ready_to_start"
    IN_PROGRESS = "in_progress"
    GAME_OVER = "game_over" # For example, less than 2 players with chips


class Table:
    """
    Class representing a single poker table (Texas Hold'em).
    Manages all game logic on the table.
    """
    def __init__(self, table_id: str, name: str, max_players: int, small_blind: float, big_blind: float, hand_evaluator: HandEvaluator): # Changed small_blind, big_blind to float
        """
        Constructor for the Table class.

        :param table_id: The table identifier (now a string).
        :param name: The name of the table.
        :param max_players: The maximum number of players that can sit at the table.
        :param small_blind: The amount of the small blind.
        :param big_blind: The amount of the big blind.
        :param hand_evaluator: HandEvaluator object for ranking hands.
        """
        self._table_id: str = table_id
        self._name: str = name 
        self._max_players: int = max_players
        self._small_blind: float = small_blind
        self._big_blind: float = big_blind

        self._status: TableStatus = TableStatus.WAITING_FOR_PLAYERS

        # Players at the table, mapped by seat number
        self._seats: Dict[int, Optional[Player]] = {i: None for i in range(1, max_players + 1)} # Seats 1 to max_players
        self._players: Dict[int, Player] = {} # {player_id: Player_object} - seated players
        
        self._viewers: Dict[int, Player] = {} # {player_id: Player_object} - viewers only

        self._deck: CardDeck = CardDeck() # ✅ Correction: Changed to Deck
        self._pot: Pot = Pot()
        self._hand_evaluator: HandEvaluator = hand_evaluator # Dependency injection

        # Current hand state
        self._community_cards: List[Card] = [] # Community cards (Flop, Turn, River)
        self._current_dealer_seat_index: int = -1 # Seat number of the current dealer
        self._current_hand_number: int = 0 # Current hand number

        self._betting_round: Optional[BettingRound] = None # Current betting round object

        logger.info(f"Table '{self._name}' (ID: {self._table_id}) initialized.") 
        print(f"Table '{self._name}' (ID: {self._table_id}) created.") 

    # --- Properties (Direct data access) ---
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
    def small_blind(self) -> float: # Changed to float
        return self._small_blind

    @property
    def big_blind(self) -> float: # Changed to float
        return self._big_blind

    @property
    def status(self) -> TableStatus:
        return self._status

    @property
    def num_seated_players(self) -> int:
        return len(self._players) # Based on the number of players in the dictionary

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

    # --- Player Management ---
    def take_seat(self, player: Player, seat_number: int, buy_in_amount: float) -> bool:
        """
        Seats a player at a specific seat on the table.
        :param player: Player object who wants to sit.
        :param seat_number: Seat number (1 to max_players).
        :param buy_in_amount: The amount of chips the player buys in for.
        :return: True if seating was successful, False otherwise.
        """
        if not (1 <= seat_number <= self._max_players):
            logger.warning(f"Seat {seat_number} is out of bounds for table {self._table_id} (max {self._max_players}).")
            return False
        
        if self._seats[seat_number] is not None:
            logger.warning(f"Seat {seat_number} on table {self._table_id} is already occupied.")
            return False
        
        # ✅ Check: if the player is already seated at this seat on this table
        if player.is_seated_at_table(self.table_id):
            logger.warning(f"Player {player.username} (ID: {player.user_id}) is already seated at table {self.table_id}. Cannot take seat again.")
            return False

        # Ensure the player has enough chips in their total account for buy-in
        if player.get_user_total_chips() < buy_in_amount:
            logger.warning(f"Player {player.username} (ID: {player.user_id}) has insufficient chips ({player.get_user_total_chips()}) for buy-in of {buy_in_amount}.")
            return False

        # ✅ Remove the player from the viewer list of *this table* if they were a viewer
        if player.is_viewing_table(self.table_id): # Use the new method of Player
            self.remove_viewer(player.user_id) # Remove them from the viewer list of this table
            logger.info(f"Player {player.username} (ID: {player.user_id}) removed from viewer list of table {self.table_id} before seating.")
        
        # Perform the buy-in
        try:
            player.perform_buy_in(self.table_id, buy_in_amount) # ✅ Pass table_id
        except ValueError as e:
            logger.error(f"Error during buy-in for player {player.username}: {e}")
            return False

        # Seat the player
        self._seats[seat_number] = player
        self._players[player.user_id] = player # Add to the list of active players at the table (keyed by player_id)
        player.set_seated_data_for_table(self._table_id, seat_number) # ✅ Correction: Use set_seated_data_for_table
        logger.info(f"Player {player.username} (ID: {player.user_id}) successfully took seat {seat_number} on table {self._table_id} with {buy_in_amount} chips.")
        print(f"Player {player.username} took seat {seat_number}.")
        
        # Update table status if there are enough players to start
        if self.num_seated_players >= 2 and self.status == TableStatus.WAITING_FOR_PLAYERS:
            self._status = TableStatus.READY_TO_START
            logger.info(f"Table {self.name} is now {self.status.value}.")
            print(f"Table {self.name} is now in state: {self.status.value}")
            
        return True

    def remove_player(self, player_id: int) -> bool: 
        """
        Removes a player from the table by their ID.
        :param player_id: The ID of the player to remove.
        :return: True if the player was successfully removed, False otherwise.
        """
        player_to_remove = self._players.get(player_id)
        if player_to_remove:
            seat_num = player_to_remove.get_seat_number(self.table_id) # ✅ Use get_seat_number
            if seat_num is not None:
                self._seats[seat_num] = None # Vacate the seat
            del self._players[player_id] # Remove from the main dictionary
            
            # TODO: Handle remaining chips for the player (return to general user account).
            player_to_remove.leave_table_position(self.table_id) # ✅ Calls method in Player to reset their state and return chips

            logger.info(f"Player {player_to_remove.username} left seat {seat_num} on table {self.table_id}.")
            print(f"Player {player_to_remove.username} left seat {seat_num}.")

            if self.num_seated_players < 2 and self.status == TableStatus.IN_PROGRESS:
                self._status = TableStatus.WAITING_FOR_PLAYERS
                logger.info(f"Table {self.name} is now {self.status.value} (not enough players).")
                print(f"Table {self.name} is now in state: {self.status.value} (not enough players).")
                if self.betting_round:
                    self._betting_round = None 
                    self._determine_winner_and_distribute_pot(skip_showdown=True)
            return True
        logger.warning(f"Error: Player with ID {player_id} not found at the table.")
        print(f"Error: Player with ID {player_id} not found at the table.")
        return False

    def get_player_by_id(self, player_id: int) -> Optional[Player]: 
        """Returns a seated player object by ID."""
        return self._players.get(player_id)

    def get_player_by_seat(self, seat_number: int) -> Optional[Player]:
        """Returns a seated player object by seat number."""
        # ✅ We will need to search by seat_number in the _seats dictionary
        return self._seats.get(seat_number)

    def get_seated_players(self) -> List[Player]:
        """
        Returns a list of all players currently seated at the table, sorted by seat number.
        """
        # ✅ The _players dictionary is now mapped by player_id, not seat_number.
        # We will need to sort by the Player object's seat_number
        # Use self._players.values() to get all seated player objects
        # Added a condition to the lambda to prevent errors if get_seat_number returns None (although it should be seated)
        return sorted([p for p in self._players.values()], key=lambda p: p.get_seat_number(self.table_id) if p.is_seated_at_table(self.table_id) else float('inf')) 
    
    def get_active_players_in_hand(self) -> List[Player]:
        """
        Returns a list of players who are still active in the current hand (not folded, not sitting out, and have chips).
        """
        return [p for p in self.get_seated_players() 
                if p.get_hand_status(self.table_id) not in [PlayerHandStatus.FOLDED, PlayerHandStatus.SITTING_OUT] # ✅ Pass table_id
                and p.get_chips_on_table(self.table_id) > 0] # ✅ Pass table_id
    
    # --- Viewer Management ---
    def add_viewer(self, viewer_player: Player) -> bool:
        """
        Adds a player to the table's viewer list.
        :param viewer_player: Player object who wants to view.
        :return: True if the viewer was successfully added, False if they are already a viewer or a player.
        """
        if viewer_player.user_id in self._viewers: 
            logger.debug(f"Viewer {viewer_player.username} (ID: {viewer_player.user_id}) is already viewing table {self.table_id}.") 
            return True 
        
        # ✅ Ensure the player is not already seated at this table
        if viewer_player.is_seated_at_table(self.table_id): # ✅ Correction: Use is_seated_at_table
            logger.warning(f"Error: Player {viewer_player.username} (ID: {viewer_player.user_id}) is already seated at seat {viewer_player.get_seat_number(self.table_id)} and cannot simultaneously be a viewer at table {self.table_id}.") # ✅ Update message
            return False

        self._viewers[viewer_player.user_id] = viewer_player 
        viewer_player.add_viewing_table(self.table_id) # ✅ Update the player's viewing status in the Player object
        logger.info(f"Viewer {viewer_player.username} (ID: {viewer_player.user_id}) added to viewer list of table {self.table_id}.") 
        print(f"Viewer {viewer_player.username} (ID: {viewer_player.user_id}) added to viewer list of table {self.table_id}.")
        return True

    def remove_viewer(self, user_id: int) -> bool: # Changed player_id to user_id
        """
        Removes a viewer from the table's viewer list.
        :param user_id: The ID of the viewer to remove.
        :return: True if the viewer was successfully removed, False otherwise.
        """
        viewer_to_remove = self._viewers.pop(user_id, None)
        if viewer_to_remove:
            viewer_to_remove.remove_viewing_table(self.table_id) # ✅ Update the player's viewing status in the Player object
            logger.info(f"Viewer with ID {user_id} removed from viewer list of table {self.table_id}.") 
            print(f"Viewer with ID {user_id} removed from viewer list of table {self.table_id}.")
            return True
        logger.warning(f"Error: Viewer with ID {user_id} not found in the viewer list of table {self.table_id}.") 
        print(f"Error: Viewer with ID {user_id} not found in the viewer list of table {self.table_id}.")
        return False
        
    def get_all_viewers(self) -> List[Player]:
        """
        Returns a list of all viewer objects at the table.
        """
        return list(self._viewers.values())

    def get_num_viewers(self) -> int:
        """
        Returns the number of viewers at the table.
        """
        return len(self._viewers) # Based on the number of viewers in the dictionary

    def get_viewer_by_id(self, user_id: int) -> Optional[Player]: # Changed player_id to user_id
        """
        Returns a viewer object by their ID.
        """
        return self._viewers.get(user_id)

    # --- Hand Management ---
    def start_new_hand(self) -> bool:
        """
        Starts a new poker hand.
        Includes shuffling cards, determining dealer, distributing blinds and cards.
        :return: True if the hand started successfully, False otherwise.
        """
        active_players = self.get_active_players_in_hand()
        if len(active_players) < 2:
            logger.info("Not enough active players with chips to start a new hand.")
            print("Not enough active players with chips to start a new hand.")
            self._status = TableStatus.READY_TO_START if self.num_seated_players >= 2 else TableStatus.WAITING_FOR_PLAYERS 
            if self.num_seated_players > 0 and len(active_players) == 0: 
                self._status = TableStatus.GAME_OVER
            return False
        
        self._status = TableStatus.IN_PROGRESS
        self._current_hand_number += 1
        logger.info(f"--- Starting new hand (# {self.current_hand_number}) ---")
        print(f"\n--- Starting new hand (# {self.current_hand_number}) ---")

        # Reset previous state
        self.pot.reset_pots() 
        self._community_cards = []
        self._deck = CardDeck() # ✅ Correction: Changed to Deck
        self._deck.shuffle()

        # Reset players' hand state and set who is sitting out
        for player in self.get_seated_players():
            player.reset_hand_state(self.table_id) # ✅ Pass table_id
            if player.get_chips_on_table(self.table_id) == 0: # ✅ Pass table_id
                player.set_hand_status(self.table_id, PlayerHandStatus.SITTING_OUT) # ✅ Pass table_id
                logger.info(f"{player.username} is sitting out (no chips).")
                print(f"{player.username} is sitting out (no chips).")
            else:
                player.set_hand_status(self.table_id, PlayerHandStatus.ACTIVE) # ✅ Pass table_id

        # Determine the next dealer
        self._set_next_dealer()

        # Deal cards to all active players
        current_active_players_for_dealing = self.get_active_players_in_hand()
        if len(current_active_players_for_dealing) < 2: 
            logger.info("Not enough active players after chip distribution.")
            print("Not enough active players after chip distribution.")
            self._status = TableStatus.READY_TO_START if self.num_seated_players >= 2 else TableStatus.WAITING_FOR_PLAYERS 
            return False


        for player in current_active_players_for_dealing:
            hand_cards = [self._deck.deal_card(), self._deck.deal_card()] # ✅ Correction: Changed to deal()
            player.set_hand(self.table_id, hand_cards) # ✅ Pass table_id
            logger.info(f"{player.username} (seat {player.get_seat_number(self.table_id)}) received: {hand_cards}") # ✅ Pass table_id
            print(f"{player.username} (seat {player.get_seat_number(self.table_id)}) received: {hand_cards}") # ✅ Pass table_id

        # Determine player order based on seating turns relative to dealer and blinds
        ordered_players_for_betting = self._get_players_in_betting_order_for_round()
        
        if not ordered_players_for_betting:
            logger.info("No players need to act in this round. Ending hand.")
            print("No players need to act in this round. Ending hand.")
            self.end_hand() 
            return False

        # Create and start the first betting round (Pre-flop)
        self._betting_round = BettingRound(
            active_players=ordered_players_for_betting, # Player order for the round
            pot=self.pot, 
            dealer_seat_index=self.current_dealer_seat_index, 
            big_blind_amount=self.big_blind 
        )
        self._betting_round.start_round(is_pre_flop=True) # Will handle blinds

        if self.betting_round.status in [BettingRoundStatus.COMPLETED, BettingRoundStatus.NO_ACTIVE_PLAYERS]: 
            self._end_current_betting_round() 
            
        return True

    def _set_next_dealer(self):
        """
        Determines the seat number of the next dealer.
        The dealer moves sequentially through active (with chips) seats.
        """
        active_seated_players = self.get_active_players_in_hand() 
        if not active_seated_players:
            self._current_dealer_seat_index = -1
            return

        # Ensure players are sorted by seat number
        active_seated_players.sort(key=lambda p: p.get_seat_number(self.table_id)) # ✅ Ensure correct sorting

        if self.current_dealer_seat_index == -1: 
            self._current_dealer_seat_index = active_seated_players[0].get_seat_number(self.table_id) # ✅ Use get_seat_number
        else:
            current_dealer_idx_in_active = -1
            for i, p in enumerate(active_seated_players):
                if p.get_seat_number(self.table_id) == self.current_dealer_seat_index: # ✅ Use get_seat_number
                    current_dealer_idx_in_active = i
                    break
            
            if current_dealer_idx_in_active == -1 or current_dealer_idx_in_active == len(active_seated_players) - 1:
                self._current_dealer_seat_index = active_seated_players[0].get_seat_number(self.table_id) # ✅ Use get_seat_number
            else:
                self._current_dealer_seat_index = active_seated_players[current_dealer_idx_in_active + 1].get_seat_number(self.table_id) # ✅ Use get_seat_number

        logger.info(f"The dealer for this hand is seat number: {self.current_dealer_seat_index}")
        print(f"The dealer for this hand is seat number: {self.current_dealer_seat_index}")


    def _get_players_in_betting_order_for_round(self) -> List[Player]:
        """
        Returns a list of active players in the hand, ordered according to poker turn order
        (starting from the player who acts first after the blinds in pre-flop, or after the dealer in post-flop).
        This is complex logic that must be precise.
        """
        all_seated_players = self.get_seated_players() 
        active_players_in_hand = [p for p in all_seated_players if p.get_hand_status(self.table_id) in [PlayerHandStatus.ACTIVE, PlayerHandStatus.ALL_IN]] # ✅ Pass table_id

        if not active_players_in_hand:
            return []

        # Ensure players are sorted by seat number
        active_players_in_hand.sort(key=lambda p: p.get_seat_number(self.table_id)) # ✅ Ensure correct sorting

        dealer_pos_in_seated = -1
        for i, p in enumerate(all_seated_players):
            if p.get_seat_number(self.table_id) == self.current_dealer_seat_index: # ✅ Use get_seat_number
                dealer_pos_in_seated = i
                break

        if dealer_pos_in_seated == -1: 
            # If the dealer is not in active_players_in_hand, this is an unusual situation, return everyone
            return active_players_in_hand 

        if len(self.community_cards) > 0 or self.current_hand_number > 0 : # Post-Flop
            # The first player to act in post-flop is the first active player to the left of the dealer
            first_to_act_index_in_seated = (dealer_pos_in_seated + 1) % len(all_seated_players) 
            
            first_player_to_act_index = -1
            num_seated = len(all_seated_players)
            for _ in range(num_seated):
                current_player = all_seated_players[first_to_act_index_in_seated]
                if current_player.get_hand_status(self.table_id) in [PlayerHandStatus.ACTIVE, PlayerHandStatus.ALL_IN]: # ✅ Pass table_id
                    first_player_to_act_index = first_to_act_index_in_seated
                    break
                first_to_act_index_in_seated = (first_to_act_index_in_seated + 1) % num_seated
            
            if first_player_to_act_index == -1: 
                return [] 
                
            ordered_for_round = []
            current_idx = first_player_to_act_index
            while True:
                player = all_seated_players[current_idx]
                if player.get_hand_status(self.table_id) in [PlayerHandStatus.ACTIVE, PlayerHandStatus.ALL_IN]: # ✅ Pass table_id
                    ordered_for_round.append(player)
                current_idx = (current_idx + 1) % num_seated
                if current_idx == first_player_to_act_index: 
                    break
            
            return ordered_for_round
            
        else: # Pre-Flop
            # In pre-flop, the first player to act is the UTG (Under The Gun)
            # which is the first active player to the left of the big blind.
            # This logic is more complex and requires identifying small/big blinds.
            # For temporary simplicity, we will return all active players in seat order.
            # TODO: Implement precise UTG logic.
            return [p for p in active_players_in_hand] # Already sorted by seat


    def _open_community_cards(self, num_cards: int):
        """
        Opens community cards (Flop, Turn, River).
        :param num_cards: Number of cards to open (3 for flop, 1 for turn/river).
        """
        if len(self._deck.get_cards()) < num_cards + 1: 
            logger.warning("Not enough cards in the deck to open additional community cards.")
            print("Not enough cards in the deck to open additional community cards.")
            return

        self._deck.deal_card() # ✅ Correction: "Burns" a card before each opening (Changed to deal())
        
        for _ in range(num_cards):
            self._community_cards.append(self._deck.deal()) # ✅ Correction: Changed to deal()
        
        logger.info(f"Community cards: {self.community_cards}")
        print(f"Community cards: {self.community_cards}")

    def process_player_action(self, player_id: int, action: PlayerAction, amount: Optional[float] = None) -> bool: # Changed amount to float
        """
        Processes a player action coming from the client.
        Passes the action to the current BettingRound object.

        :param player_id: The player's ID.
        :param action: The type of action.
        :param amount: The bet amount (if applicable).
        :return: True if the action was performed, False otherwise.
        """
        if self.status != TableStatus.IN_PROGRESS or not self.betting_round: 
            logger.warning(f"Error: Cannot perform action when table is in state {self.status.value} or no active betting round.") 
            print(f"Error: Cannot perform action when table is in state {self.status.value} or no active betting round.")
            return False

        current_player = self.betting_round.current_player 
        if not current_player or current_player.user_id != player_id: 
            logger.warning(f"Error: It is not player {player_id}'s turn to act.")
            print(f"Error: It is not player {player_id}'s turn to act.")
            return False

        # ✅ Pass the Player object and table_id to the BettingRound's process_action method
        success = self.betting_round.process_action(current_player, action, amount, self.table_id) 
        
        if success and (self.betting_round.status == BettingRoundStatus.COMPLETED or \
           self.betting_round.status == BettingRoundStatus.NO_ACTIVE_PLAYERS): 
            self._end_current_betting_round() 
            
        return success

    def _end_current_betting_round(self):
        """
        Ends the current betting round and collects money into the pot.
        """
        if not self.betting_round: 
            return

        self.betting_round.end_round_and_collect_bets() 
        self._betting_round = None 

        self._advance_hand_phase()


    def _advance_hand_phase(self):
        """
        Advances the hand phase (Pre-flop -> Flop -> Turn -> River -> Showdown).
        """
        active_players_count = len(self.get_active_players_in_hand())
        if active_players_count <= 1:
            self._determine_winner_and_distribute_pot(skip_showdown=True)
            return

        current_community_cards_count = len(self.community_cards) 

        if current_community_cards_count == 0: 
            logger.info("\n--- FLOP Phase ---")
            print("\n--- FLOP Phase ---")
            self._open_community_cards(3) 
            self._start_new_betting_round()
        elif current_community_cards_count == 3: 
            logger.info("\n--- TURN Phase ---")
            print("\n--- TURN Phase ---")
            self._open_community_cards(1) 
            self._start_new_betting_round()
        elif current_community_cards_count == 4: 
            logger.info("\n--- RIVER Phase ---")
            print("\n--- RIVER Phase ---")
            self._open_community_cards(1) 
            self._start_new_betting_round()
        elif current_community_cards_count == 5: 
            logger.info("\n--- SHOWDOWN Phase ---")
            print("\n--- SHOWDOWN Phase ---")
            self._determine_winner_and_distribute_pot()
        else:
            logger.warning("Error: Unknown or invalid hand phase.")
            print("Error: Unknown or invalid hand phase.")
            self.end_hand() 


    def _start_new_betting_round(self):
        """
        Starts a new betting round after community cards are opened.
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
        Determines the winner (or winners) and distributes the pot.
        :param skip_showdown: True if only one player remains (then no Showdown).
        """
        logger.info("\n--- Determining Winner and Distributing Pot ---")
        print("\n--- Determining Winner and Distributing Pot ---")
        
        # This logic must include handling Side Pots
        # which is currently not fully implemented in the Pot class.
        # This is one of the most complex parts of poker simulation.
        # For now, we will focus on simple distribution of the main pot.

        # Step 1: Identify relevant players (those remaining in the hand)
        players_in_showdown = [p for p in self.get_seated_players() if p.get_hand_status(self.table_id) in [PlayerHandStatus.ACTIVE, PlayerHandStatus.ALL_IN]] # ✅ Pass table_id
        
        if skip_showdown and len(players_in_showdown) == 1:
            winner = players_in_showdown[0]
            winnings = self.pot.get_total_pot_size() # ✅ Correction: Get pot amount
            winner.add_chips_to_table(self.table_id, winnings) # ✅ Pass table_id
            logger.info(f"Player {winner.username} won the pot of {winnings} chips (hand ended early).")
            print(f"Player {winner.username} won the pot of {winnings} chips (hand ended early).")
            self.end_hand()
            return

        if not players_in_showdown:
            logger.warning("No active players to determine a winner.")
            print("No active players to determine a winner.")
            self.end_hand()
            return

        # Step 2: Hand Ranking
        # Create a list of hands to rank
        hands_to_evaluate = []
        for player in players_in_showdown:
            # Ensure the player has cards in hand
            if player.get_hand(self.table_id): # ✅ Pass table_id
                hands_to_evaluate.append({
                    'player_id': player.user_id,
                    'player_name': player.username,
                    'hand_cards': player.get_hand(self.table_id), # ✅ Pass table_id
                    'community_cards': self.community_cards
                })
            else:
                logger.warning(f"Player {player.username} (ID: {player.user_id}) has no cards in hand during Showdown.")

        if not hands_to_evaluate:
            logger.warning("No hands to rank during Showdown.")
            print("No hands to rank during Showdown.")
            self.end_hand()
            return

        # Call HandEvaluator
        ranked_hands = self._hand_evaluator.rank_hands(hands_to_evaluate)

        if not ranked_hands:
            logger.error("HandEvaluator did not return ranked hands.")
            print("HandEvaluator did not return ranked hands.")
            self.end_hand()
            return

        # Step 3: Side Pot Distribution - Complex Logic
        # For simplicity for now, we will only consider the main pot.
        
        # Find the best hand (or best hands in case of a tie)
        best_rank = ranked_hands[0]['rank_value']
        winning_hands = [h for h in ranked_hands if h['rank_value'] == best_rank]

        if len(winning_hands) == 1:
            # Single winner
            winner_info = winning_hands[0]
            winner_player = self.get_player_by_id(winner_info['player_id'])
            if winner_player:
                winnings = self.pot.get_total_pot_size() # ✅ Correction: Get pot amount
                winner_player.add_chips_to_table(self.table_id, winnings) # ✅ Pass table_id
                logger.info(f"Player {winner_player.username} won the pot of {winnings} chips with {winner_info['hand_name']}.")
                print(f"Player {winner_player.username} won the pot of {winnings} chips with {winner_info['hand_name']}.")
            else:
                logger.error(f"Winner with ID {winner_info['player_id']} not found as a Player object.")
        else:
            # Tie between multiple players
            num_winners = len(winning_hands)
            split_amount = self.pot.get_total_pot_size() // num_winners # ✅ Correction: Get pot amount
            logger.info(f"Tie between {num_winners} players. Each receives {split_amount} chips.")
            print(f"Tie between {num_winners} players. Each receives {split_amount} chips.")
            for winner_info in winning_hands:
                winner_player = self.get_player_by_id(winner_info['player_id'])
                if winner_player:
                    winner_player.add_chips_to_table(self.table_id, split_amount) # ✅ Pass table_id
                    logger.info(f"Player {winner_player.username} received {split_amount} chips (tied with {winner_info['hand_name']}).")
                    print(f"Player {winner_player.username} received {split_amount} chips (tied with {winner_info['hand_name']}).")
                else:
                    logger.error(f"Winner with ID {winner_info['player_id']} not found as a Player object.")
            # Handle remainder if any
            remainder = self.pot.get_total_pot_size() % num_winners # ✅ Correction: Get pot amount
            if remainder > 0:
                logger.info(f"Remaining {remainder} chips in the pot (tie remainder).")
                print(f"Remaining {remainder} chips in the pot (tie remainder).")
                # TODO: Handle remainder - usually goes to the first player to the left of the dealer.

        self.end_hand()

    def end_hand(self):
        """
        Ends the current hand and prepares the table for the next hand.
        """
        logger.info("--- Hand End ---")
        print("--- Hand End ---")
        self._community_cards = []
        self._deck = CardDeck() # ✅ Correction: Changed to Deck
        self.pot.reset_pots()
        self._betting_round = None

        # Reset hand state for all seated players
        for player in self.get_seated_players():
            player.reset_hand_state(self.table_id) # ✅ Pass table_id
            # If player is sitting out
