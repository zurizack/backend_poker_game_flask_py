from typing import List, Dict, Optional, Tuple
import enum

# Import previous classes
from backend.poker_server.game.engine.player_oop import Player
from backend.poker_server.game.engine.pot import Pot # We will need Pot to transfer bets to it
from backend.poker_server.game.engine.player_hand import PlayerAction, PlayerHandStatus # For player statuses and actions


class BettingRoundStatus(enum.Enum):
    """
    Possible statuses for a betting round.
    """
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NO_ACTIVE_PLAYERS = "no_active_players" # All players folded except one


class BettingRound:
    """
    A class that manages a single betting round in a poker game (e.g., Pre-flop, Flop, Turn, River).
    """
    def __init__(self, active_players: List[Player], pot: Pot, dealer_seat_index: int, big_blind_amount: int):
        """
        Constructor for the BettingRound class.

        :param active_players: A list of active Player objects (who haven't folded or sat out) at the start of the round.
                               This list should be ordered according to seating turns at the table, starting from the first player to act.
        :param pot: A Pot object managing the game's pot.
        :param dealer_seat_index: The seat index of the dealer. Used to determine the order of actions.
        :param big_blind_amount: The amount of the big blind. Used to determine the minimum bet.
        """
        if not active_players:
            raise ValueError("Betting round must start with active players.")
        
        self._active_players: List[Player] = active_players
        self._pot: Pot = pot
        self._dealer_seat_index: int = dealer_seat_index # Dealer's seat index
        self._big_blind_amount: int = big_blind_amount

        # Round status
        self._status: BettingRoundStatus = BettingRoundStatus.IN_PROGRESS
        
        # The highest bet paid by any player in the current round.
        # Starts at 0, or at the big blind in the pre-flop round.
        self._current_max_bet_in_round: int = 0 
        
        # Index of the current player to act within the _active_players list.
        self._current_player_index: int = 0 
        
        # Amount bet by each player *in the current round* (not cumulative)
        self._player_round_bets: Dict[str, int] = {p.get_user_id(): 0 for p in active_players}

        # Has anyone raised/bet this round yet?
        self._raised_this_round: bool = False
        
        # The difference between the highest bet and the second highest bet, or the big blind.
        # This is the value of the last "raise amount".
        self._last_raise_amount: int = self._big_blind_amount # Default
        
        # Players who still need to act (e.g., after a raise).
        # We will store their user_id.
        self._players_to_act: List[str] = [p.get_user_id() for p in active_players]
        # We will store the starting point of the action round (who started the round/last raise)
        self._round_starter_id: Optional[str] = None 
        
        # The total amount a player has invested in the entire hand (not just this round)
        # We will need to get this from the Player object itself or manage it here
        # Currently, we will use player.get_current_bet() which is cumulative.

    def start_round(self, is_pre_flop: bool = False):
        """
        Starts the betting round.
        Handles blinds if necessary.
        """
        print(f"Starting new betting round. Active players: {[p.get_username() for p in self._active_players]}")

        if is_pre_flop:
            # In pre-flop, blinds are the first bets
            self._handle_blinds()
        
        # Determine the first player to act
        self._set_first_player_to_act()
        self._round_starter_id = self._active_players[self._current_player_index].get_user_id()
        self._status = BettingRoundStatus.IN_PROGRESS

        if len(self._active_players) == 1:
            self._status = BettingRoundStatus.NO_ACTIVE_PLAYERS # If only one player remains, the round is over.


    def _handle_blinds(self):
        """
        Handles blind bets at the beginning of pre-flop.
        (Assumption: Players in the _active_players list are ordered after the dealer,
        so Small Blind and Big Blind will be positioned correctly).
        """
        # TODO: Implement accurate blind posting logic.
        # This requires knowing the positions (SB, BB) based on dealer position.
        # For now, a simplified example:
        if len(self._active_players) >= 2:
            # Assume the player after the dealer is the SB and the next is the BB.
            # This requires logic to find the actual SB/BB.
            # For now, we'll just take the first 2 players in order (not necessarily correct for real poker)

            # Assume _active_players is already sorted by turn, including blinds at the beginning
            
            # Small Blind
            sb_player = self._active_players[0]
            sb_amount = self._big_blind_amount // 2
            if sb_player.can_afford(sb_amount):
                sb_player.remove_chips_from_table(sb_amount)
                sb_player.add_to_current_bet(sb_amount) # Adds to total bet in hand
                self._player_round_bets[sb_player.get_user_id()] += sb_amount
                # self._pot.add_bet(sb_player, sb_amount, self._current_max_bet_in_round) # Add to pot in collect_round_bets
                print(f"{sb_player.get_username()} posted Small Blind: {sb_amount}")
            else:
                # Went all-in on the Small Blind
                sb_player.go_all_in()
                sb_amount = sb_player.get_current_bet() # The actual amount put in
                self._player_round_bets[sb_player.get_user_id()] += sb_amount
                print(f"{sb_player.get_username()} went All-In on Small Blind: {sb_amount}")
            
            # Big Blind
            if len(self._active_players) >= 2:
                bb_player = self._active_players[1]
                bb_amount = self._big_blind_amount
                if bb_player.can_afford(bb_amount):
                    bb_player.remove_chips_from_table(bb_amount)
                    bb_player.add_to_current_bet(bb_amount) # Adds to total bet in hand
                    self._player_round_bets[bb_player.get_user_id()] += bb_amount
                    # self._pot.add_bet(bb_player, bb_amount, self._current_max_bet_in_round)
                    print(f"{bb_player.get_username()} posted Big Blind: {bb_amount}")
                else:
                    # Went all-in on the Big Blind
                    bb_player.go_all_in()
                    bb_amount = bb_player.get_current_bet()
                    self._player_round_bets[bb_player.get_user_id()] += bb_amount
                    print(f"{bb_player.get_username()} went All-In on Big Blind: {bb_amount}")
                
                # Update the maximum bet in the round
                self._current_max_bet_in_round = max(self._current_max_bet_in_round, bb_amount)
        
        # After blinds, collect bets into the pot
        self._pot.collect_round_bets(self._player_round_bets, {p.get_user_id(): p.get_current_bet() for p in self._active_players})
        self._player_round_bets = {p.get_user_id(): 0 for p in self._active_players} # Reset round bets


    def _set_first_player_to_act(self):
        """
        Determines the first player to act in the round.
        In pre-flop, it's the player located after the Big Blind.
        In subsequent rounds, it's the first active player after the dealer (or the dealer himself if he's active).
        """
        # TODO: Implement accurate first player logic for each round type.
        # This is complex as it depends on dealer position and active players.
        
        # For now, assume players are already sorted by turn,
        # and in pre-flop, we start from index 2 (after SB and BB, if they exist).
        # In post-flop, we start from the first in the active players list.

        if len(self._active_players) > 0:
            # In pre-flop, the position of the first player after the blinds
            # In post-flop, the position of the first active player after the dealer (the button)
            self._current_player_index = 0 # Start from the first in the list for now

            # Ensure _active_players is sorted in the correct turn order before passing to the class
            # This will be the responsibility of the Table class.
            
            # Find the dealer's position in the active players list
            dealer_active_index = -1
            for i, p in enumerate(self._active_players):
                if p.get_seat_number() == self._dealer_seat_index:
                    dealer_active_index = i
                    break

            if dealer_active_index != -1:
                # In post-flop, the turn starts from the first active player after the dealer
                # or the dealer himself if everyone folded after him and he's the only player left
                # The index of who needs to act will be (dealer_active_index + 1) % len(self._active_players)
                # And search for the first active player from there
                
                # For now, just leave it as 0. (This point requires specific handling)
                pass


    def get_current_player(self) -> Optional[Player]:
        """
        Returns the Player object whose turn it is to act.
        """
        if self._status != BettingRoundStatus.IN_PROGRESS or not self._active_players:
            return None
        
        # Ensure the index is valid
        if 0 <= self._current_player_index < len(self._active_players):
            return self._active_players[self._current_player_index]
        return None

    def get_current_max_bet(self) -> int:
        """
        Returns the maximum bet amount placed in this round so far.
        """
        return self._current_max_bet_in_round

    def get_call_amount(self, player: Player) -> int:
        """
        Returns the amount the player needs to complete to CALL.
        :param player: The player object.
        """
        # The total amount the player has already put in the hand
        player_total_bet = player.get_current_bet()
        
        # The amount to complete is the maximum bet minus what the player has already put in
        amount_to_call = self._current_max_bet_in_round - player_total_bet
        
        # If the amount is negative (already bet more), or zero, then no CALL is needed.
        return max(0, amount_to_call)

    def get_min_raise_amount(self) -> int:
        """
        Returns the minimum allowed raise amount.
        This is usually the big blind, or the size of the last raise if it was larger.
        """
        return max(self._big_blind_amount, self._last_raise_amount)

    def process_action(self, player_id: str, action: PlayerAction, amount: Optional[int] = None) -> bool:
        """
        Processes a player's action in the betting round.

        :param player_id: The ID of the player performing the action.
        :param action: The player's action (CHECK, CALL, RAISE, FOLD, ALL_IN).
        :param amount: The bet amount (relevant for RAISE).
        :return: True if the action was successful, False otherwise.
        """
        current_player = self.get_current_player()
        if not current_player or current_player.get_user_id() != player_id:
            print(f"Error: It's not player {player_id}'s turn to act.")
            return False

        # Cannot act if the player has already folded or is all-in
        if current_player.get_hand_status() in [PlayerHandStatus.FOLDED, PlayerHandStatus.ALL_IN]:
            print(f"Error: Player {current_player.get_username()} is already in {current_player.get_hand_status().value} state.")
            return False

        current_player_total_bet_in_hand = current_player.get_current_bet() # The total amount the player has put in the hand
        amount_to_call = self._current_max_bet_in_round - current_player_total_bet_in_hand
        
        print(f"{current_player.get_username()} attempting action: {action.value} with amount: {amount if amount is not None else 'N/A'}")

        if action == PlayerAction.FOLD:
            current_player.fold()
            print(f"{current_player.get_username()} folded the hand.")
            
        elif action == PlayerAction.CHECK:
            if amount_to_call > 0:
                print(f"Error: Cannot CHECK when there is a bet to call ({amount_to_call} chips).")
                return False
            current_player.set_last_action(PlayerAction.CHECK)
            print(f"{current_player.get_username()} checked.")
            
        elif action == PlayerAction.CALL:
            if not current_player.can_afford(amount_to_call):
                print(f"Error: {current_player.get_username()} cannot afford to CALL. Missing {amount_to_call - current_player.get_chips_on_table()} chips.")
                return False
            
            # Remove chips from player's stack and add to their bet in hand
            current_player.remove_chips_from_table(amount_to_call)
            current_player.add_to_current_bet(amount_to_call)
            self._player_round_bets[player_id] += amount_to_call # Record how much was put in this round
            current_player.set_last_action(PlayerAction.CALL)
            print(f"{current_player.get_username()} called to {self._current_max_bet_in_round}.")

        elif action == PlayerAction.BET or action == PlayerAction.RAISE:
            if amount is None or amount <= 0:
                print("Error: Bet/raise amount must be positive.")
                return False

            if action == PlayerAction.BET and self._current_max_bet_in_round > 0:
                print("Error: Cannot BET when a bet already exists. Use RAISE.")
                return False
            
            # The total amount of the player if they perform the action (current bet in hand + current action amount)
            total_bet_if_actioned = current_player_total_bet_in_hand + amount

            # Legality checks for BET/RAISE
            # 1. Does the player have enough chips?
            if not current_player.can_afford(amount):
                print(f"Error: {current_player.get_username()} cannot afford to bet/raise {amount} chips.")
                return False
            
            # 2. Is the new bet higher than the current maximum bet?
            #    (Unless it's an all-in for less)
            if total_bet_if_actioned < self._current_max_bet_in_round:
                print(f"Error: New bet ({total_bet_if_actioned}) is lower than current bet ({self._current_max_bet_in_round}).")
                return False

            # 3. Is the raise large enough?
            #    The difference between the new bet and the current maximum bet (this is the actual raise size)
            actual_raise_amount = total_bet_if_actioned - self._current_max_bet_in_round
            min_raise_required = self.get_min_raise_amount()

            if actual_raise_amount < min_raise_required and current_player.get_chips_on_table() > amount:
                print(f"Error: Raise is too small. Minimum raise is {min_raise_required} chips. Your raise: {actual_raise_amount}.")
                return False

            # Remove chips and update player's bet
            current_player.remove_chips_from_table(amount)
            current_player.add_to_current_bet(amount)
            self._player_round_bets[player_id] += amount

            # Update the maximum bet in the round and the last raise amount
            if total_bet_if_actioned > self._current_max_bet_in_round:
                self._last_raise_amount = total_bet_if_actioned - self._current_max_bet_in_round # Actual raise size
                self._current_max_bet_in_round = total_bet_if_actioned
                self._raised_this_round = True
                self._round_starter_id = player_id # Whoever raised is the next stopping point
                print(f"{current_player.get_username()} RAISED to {self._current_max_bet_in_round} (total bet in hand: {current_player.get_current_bet()}).")
                
            current_player.set_last_action(action)
            
        elif action == PlayerAction.ALL_IN:
            # Player goes all-in
            all_in_amount_from_chips = current_player.get_chips_on_table() # How many chips left on their seat
            
            # The All-In logic in Player should handle transferring all chips from seat to total bet in hand
            current_player.go_all_in() 
            
            # The total amount the player has put in the hand now (after all-in)
            player_total_bet_in_hand_after_all_in = current_player.get_current_bet()

            # If this All-In is higher than the current maximum bet, it's considered a raise
            if player_total_bet_in_hand_after_all_in > self._current_max_bet_in_round:
                self._last_raise_amount = player_total_bet_in_hand_after_all_in - self._current_max_bet_in_round # The size of the all-in "raise"
                self._current_max_bet_in_round = player_total_bet_in_hand_after_all_in
                self._raised_this_round = True 
                self._round_starter_id = player_id # All-in also resets the action turn
            
            # How many chips were added in this round, from the All-In
            # This is the difference between their total bet in hand now and their total bet before this All-In
            # (or simply how many chips they had on their seat before the action, if they weren't partially ALL-IN)
            self._player_round_bets[player_id] += all_in_amount_from_chips # Add how many new chips were put into the round
            
            print(f"{current_player.get_username()} went ALL-IN with {all_in_amount_from_chips} chips (total in hand: {player_total_bet_in_hand_after_all_in}).")

        else:
            print(f"Invalid action: {action.value}")
            return False

        # Advance to the next player after a successful action
        self._advance_to_next_player()
        self._check_round_completion()
        
        return True

    def _advance_to_next_player(self):
        """
        Advances the turn to the next active player.
        Skips players who folded or are all-in.
        """
        num_players = len(self._active_players)
        if num_players == 0:
            self._status = BettingRoundStatus.NO_ACTIVE_PLAYERS
            return

        original_index = self._current_player_index
        # Find the current round_starter_id's position in the active players list
        current_round_starter_player = next((p for p in self._active_players if p.get_user_id() == self._round_starter_id), None)
        
        # If there's no one who started the round, or the current player is the last and everyone called
        if current_round_starter_player is None: # Or in a state where the round started with no raise, so no "resetter"
            pass # Continue as normal, check_round_completion will determine completion

        while True:
            self._current_player_index = (self._current_player_index + 1) % num_players
            next_player = self._active_players[self._current_player_index]

            # Stopping condition: We've returned to the player who started the round / made the last raise
            # and all players in between have already acted, called, or gone all-in.
            if next_player.get_user_id() == self._round_starter_id:
                # Need to check if everyone called or went all-in
                all_matched_or_all_in = True
                for p in self._active_players: # Check everyone
                    if p.get_hand_status() == PlayerHandStatus.ACTIVE and p.get_current_bet() < self._current_max_bet_in_round:
                        all_matched_or_all_in = False
                        break
                
                if all_matched_or_all_in:
                    # All active players (who haven't folded) have matched the maximum bet or gone all-in.
                    # And the turn has returned to the starting point of the round/last raise.
                    # This is a condition for the round to end.
                    break 
                
            # Only active players (not folded, not sat out) need to act
            # An ALL_IN player does not need to act again
            if next_player.get_hand_status() == PlayerHandStatus.ACTIVE:
                # If an active player and has not yet matched the maximum bet, it's their turn
                if next_player.get_current_bet() < self._current_max_bet_in_round:
                    return # Found a player who needs to act
                elif next_player.get_current_bet() == self._current_max_bet_in_round and self._raised_this_round:
                    # If there was a raise in the round, and a player called but it's their turn again because someone else raised after them
                    # and they are not the _round_starter_id, then they need to act.
                    # But if they are the _round_starter_id, then the round is over.
                    pass # The round_starter_id logic already caught this above
                else: # current_max_bet_in_round == 0 or the player already called (and no raise after them)
                    pass # Continue searching

            # If we've iterated through everyone and all "active" players have called, or folded, or all-in (and no longer need to act),
            # and we've returned to the starting point, the round is over.
            # The logic above with next_player.get_user_id() == self._round_starter_id should handle this.
            # If we reached here without finding a player to act, it means the round is over.
            # This is handled in check_round_completion.

    def _check_round_completion(self):
        """
        Checks if the betting round has ended.
        The round ends when:
        1. All players except one have folded (then the remaining player wins the pot).
        2. All active players have matched the current maximum bet,
           and the turn has returned to the player who started the action round (or made the last raise).
           (Excluding players who went all-in for less).
        """
        active_players_in_round = [p for p in self._active_players 
                                   if p.get_hand_status() == PlayerHandStatus.ACTIVE or 
                                   p.get_hand_status() == PlayerHandStatus.ALL_IN]

        if len(active_players_in_round) <= 1: 
            if len(active_players_in_round) == 1 and active_players_in_round[0].get_hand_status() == PlayerHandStatus.FOLDED:
                # This should not happen if active players are defined correctly.
                self._status = BettingRoundStatus.COMPLETED # Round ended, single player remaining wins.
            else:
                self._status = BettingRoundStatus.NO_ACTIVE_PLAYERS # Only one player or fewer remaining
            print(f"Betting round ended: {self._status.value}")
            return

        # Check if everyone called or went all-in
        all_players_matched_or_all_in = True
        for player in active_players_in_round:
            # An active player must match the maximum bet
            if player.get_hand_status() == PlayerHandStatus.ACTIVE and \
               player.get_current_bet() < self._current_max_bet_in_round:
                all_players_matched_or_all_in = False
                break
        
        # If everyone called or all-in, and the turn returned to the starting point of the round/last raise
        if all_players_matched_or_all_in and \
           (self._current_player_index >= len(self._active_players) or self._active_players[self._current_player_index].get_user_id() == self._round_starter_id):
            self._status = BettingRoundStatus.COMPLETED
            print(f"Betting round ended: Everyone called or all-in, and turn returned to starting point. Status: {self._status.value}")
        else:
            # If not ended, it's still IN_PROGRESS
            print(f"Betting round still active. Player to act: {self.get_current_player().get_username()}")


    def end_round_and_collect_bets(self):
        """
        Ends the round, collects all current round bets into the pot,
        and resets players' round bets.
        Called at the end of each betting round (before dealing new cards, or at the end of the hand).
        """
        # Ensure the round has ended before collecting bets
        if self._status == BettingRoundStatus.IN_PROGRESS:
            print("Warning: Attempting to end an active betting round. Forcing completion.")
            # In a real scenario, we would raise an error or wait for it to complete.
            # For this case, if we reached here by mistake while it's IN_PROGRESS, we'll complete it.
            self._check_round_completion() # Ensure it transitions to COMPLETED or NO_ACTIVE_PLAYERS

        print("Collecting bets from the current round into the main pot.")
        
        # Step 1: Actual collection of bets
        all_players_total_bets_in_hand = {p.get_user_id(): p.get_current_bet() for p in self._active_players}
        self._pot.collect_round_bets(self._player_round_bets, all_players_total_bets_in_hand)

        # Step 2: Reset players' round bets
        for player in self._active_players:
            self._player_round_bets[player.get_user_id()] = 0 # Resets what they put in this round

        print(f"Total pot size now: {self._pot.get_total_pot_size()}")


    def get_status(self) -> BettingRoundStatus:
        """Returns the current status of the betting round."""
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
