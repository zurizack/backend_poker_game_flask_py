from typing import List, Dict, Tuple, Optional, Any
from poker_server.game.engine.player_oop import Player 
from poker_server.game.engine.chip_stack import Chips 


class Pot:
    """
    A class that manages the Pots on the table.
    Responsible for accumulating bets, creating Side Pots
    in case of all-ins, and distributing the pots to winning players.
    Money management in pots is currently done using dedicated Chips objects.
    """
    def __init__(self):
        """
        Constructor for the Pot class.
        Resets the main pot and the list of side pots.
        """
        self._main_pot_chips: Chips = Chips(0) 
        # Each side pot will be a dictionary:
        # {
        #   'amount_chips': Chips,          # Chips object for the amount of money in the side pot
        #   'eligible_players_ids': List[str], # List of player_id for players eligible to win this pot
        #   'all_in_bet_level': int         # The maximum bet amount placed for this pot
        # }
        self._side_pots: List[Dict] = []

    def _create_new_side_pot(self, all_in_bet_level: int, eligible_players: List[Player]):
        """
        Internal helper function for creating a new side pot.
        :param all_in_bet_level: The bet level that led to the creation of this pot (the amount an all-in player put in).
        :param eligible_players: List of players eligible to win this pot.
        """
        eligible_ids = [player.user_id for player in eligible_players if isinstance(player, Player)] # Using player.user_id
        self._side_pots.append({
            'amount_chips': Chips(0), 
            'eligible_players_ids': eligible_ids,
            'all_in_bet_level': all_in_bet_level
        })

    def add_bet(self, player: Player, bet_amount: int, current_round_max_bet: int):
        """
        Adds a player's bet to the pots.
        This method handles the logic of main and side pots in all-in situations.

        :param player: The Player object making the bet.
        :param bet_amount: The total amount the player has bet so far in this hand.
        :param current_round_max_bet: The highest bet paid by an opposing player in this betting round.
        """
        # This is a complex method that will require very delicate logic for Side Pots.
        # At this stage, we will leave the complex Side Pots logic within TODOs
        # and focus on the basic structure.
        
        # Simple and initial logic:
        # Any new bet received goes into the main pot, if there are no side pots.
        # If there are side pots, the money needs to be routed correctly.
        
        # Assuming `bet_amount` is the amount the player put in *this betting round*.
        self._main_pot_chips.add(bet_amount) 

        # TODO: Implement full Side Pot contribution logic here.
        # This will involve iterating through existing side pots and allocating
        # `bet_amount` based on `all_in_bet_level` and player eligibility.
        # If `bet_amount` exceeds existing pot levels, new side pots might be needed.

    def collect_round_bets(self, current_player_bets: Dict[int, int], all_players_total_bets_in_hand: Dict[int, int]): # Changed from str to int for player_id
        """
        Collects bets from the current betting round and distributes them to the appropriate pots,
        while managing side pots.

        :param current_player_bets: A dictionary of {player_id: amount_bet_in_this_round}
                                     The amount each player bet *in the current round*.
        :param all_players_total_bets_in_hand: A dictionary of {player_id: total_amount_bet_in_hand_so_far}
                                                     The total amount each player has bet *in this hand* (cumulative).
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
        Distributes the pots to the winning players.
        The class should also handle the case of splitting a pot among multiple winners.

        :param winning_hands: A list of tuples, where each tuple contains:
                                 (winning Player object, winning amount from the total pot, reason for winning/description)
                                 **Note:** The amount_to_win will be calculated in advance outside this class.
        """
        if not winning_hands:
            print("No winners to distribute pot to.")
            return

        # TODO: Implement complex Side Pot distribution logic here.
        # This will involve iterating through side pots (likely sorted by all_in_bet_level)
        # and distributing their `amount_chips` to eligible winners first,
        # before distributing the main pot.

        # For now, main pot distribution:
        total_main_pot_amount = self._main_pot_chips.get_amount()
        total_winnings_requested = sum(amount for _, amount, _ in winning_hands)

        if total_winnings_requested > total_main_pot_amount:
            print(f"Warning: Requested winning amount ({total_winnings_requested}) is greater than the main pot ({total_main_pot_amount}).")
            # In a real situation, this should be handled more intelligently (e.g., distribute proportionally).

        for player, amount, reason in winning_hands:
            if player: 
                try:
                    self._main_pot_chips.remove(amount) 
                    player.add_chips_to_table(amount)    
                    print(f"Player {player.username} (ID: {player.user_id}) won {amount} chips. Reason: {reason}")
                except ValueError as e:
                    print(f"Error distributing chips to player {player.username}: {e}")

        self._main_pot_chips = Chips(0) 

    def reset_pots(self):
        """
        Resets all pots for a new hand.
        """
        self._main_pot_chips = Chips(0) 
        self._side_pots = []

    def get_total_pot_size(self) -> int:
        """
        Returns the total size of all pots (main and side).
        """
        total_size = self._main_pot_chips.get_amount() 
        for pot_data in self._side_pots:
            total_size += pot_data['amount_chips'].get_amount() 
        return total_size

    def __str__(self) -> str:
        """
        Returns a readable representation of the pot status.
        """
        s = f"Main Pot: {self._main_pot_chips.get_amount()} chips" 
        if self._side_pots:
            s += "\n    Side Pots:"
            for i, sp in enumerate(self._side_pots):
                eligible_names = ", ".join(str(id) for id in sp['eligible_players_ids']) # Ensure ID is string for join
                s += (f"\n      {i+1}. Amount: {sp['amount_chips'].get_amount()} (Bet Level: {sp['all_in_bet_level']}) " 
                      f"- Eligible: [{eligible_names}]")
        return s

    def __repr__(self) -> str:
        """
        Returns an unambiguous representation of the object, used for debugging.
        """
        return (
            f"Pot(main_pot_chips={repr(self._main_pot_chips)}, side_pots={self._side_pots})" 
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the Pot object to a dictionary suitable for JSON serialization.
        """
        side_pots_data = []
        for sp in self._side_pots:
            side_pots_data.append({
                'amount': sp['amount_chips'].get_amount(), # Get the numerical value of chips
                'eligible_players_ids': sp['eligible_players_ids'],
                'all_in_bet_level': sp['all_in_bet_level']
            })

        return {
            'main_pot_amount': self._main_pot_chips.get_amount(), # Get the numerical value
            'total_pot_amount': self.get_total_pot_size(), # Get the total numerical value
            'side_pots': side_pots_data
        }
