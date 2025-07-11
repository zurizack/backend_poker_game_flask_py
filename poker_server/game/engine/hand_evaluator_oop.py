import enum
from typing import List, Tuple, Dict, Any, Optional
from collections import Counter
from itertools import combinations

# Ensure you have imported Card, Suit, Rank correctly.
from backend.poker_server.game.engine.card_oop import Card


class HandRank(enum.Enum):
    """
    Possible poker hand rankings, from lowest to highest.
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
    A class whose purpose is to evaluate poker hands (Texas Hold'em) and determine their strength.
    """
    def __init__(self):
        pass

    def evaluate_hand(self, player_cards: List[Card], community_cards: List[Card]) -> Tuple[HandRank, List[Card], List[Card]]:
        """
        Evaluates the best hand a player can make from their hole cards and community cards.
        The method tries to find the strongest hand from all 5 possible cards.

        :param player_cards: List of the player's 2 cards.
        :param community_cards: List of 3, 4, or 5 community cards.
        :return: A tuple containing:
                     1. HandRank: The hand ranking (e.g., HandRank.STRAIGHT).
                     2. List[Card]: List of the 5 cards that make up the best hand.
                     3. List[Card]: List of "kicker" cards (if relevant, otherwise empty).
        """
        all_7_cards = sorted(player_cards + community_cards, key=lambda c: c.rank.value, reverse=True) # Sort descending by rank

        best_rank = HandRank.HIGH_CARD
        best_5_cards: List[Card] = []
        best_kickers: List[Card] = []

        # Check all 21 possible combinations of 5 cards out of the 7
        # and keep the strongest hand.
        for combo in combinations(all_7_cards, 5):
            current_5_cards = sorted(list(combo), key=lambda c: c.rank.value, reverse=True)
            
            # Check the hand type for the current 5-card combination
            rank, hand_cards, kickers = self._get_hand_type_and_cards(current_5_cards)

            # If the current hand is better than the best found so far, or it's of the same type
            # and better (e.g., a higher pair), update the best hand.
            if rank.value > best_rank.value:
                best_rank = rank
                best_5_cards = hand_cards
                best_kickers = kickers
            elif rank.value == best_rank.value:
                # If the rank is the same, we need to compare the hands themselves (including kickers)
                # We will use compare_hands, but need to ensure it receives the correct format
                # compare_hands expects a tuple of (rank, cards, kickers)
                if self.compare_hands((rank, hand_cards, kickers), (best_rank, best_5_cards, best_kickers)) == 1:
                    best_rank = rank
                    best_5_cards = hand_cards
                    best_kickers = kickers
        
        # Since _get_hand_type_and_cards already returns the best 5 cards,
        # and evaluate_hand takes the best 5 cards out of 7,
        # best_kickers might not be defined correctly or at all.
        # Therefore, we will change the format of _get_hand_type_and_cards to return only the rank and the 5 cards.
        # And finally, the kickers will be calculated from the original 7 cards relative to the 5 selected hand cards.
        
        # We will modify evaluate_hand to take the best 5 cards, then calculate kickers from the rest.
        # This is a bit complex, so for now we will return empty kickers. (Requires specific implementation)
        
        return best_rank, best_5_cards, best_kickers


    def _get_hand_type_and_cards(self, cards: List[Card]) -> Tuple[HandRank, List[Card], List[Card]]:
        """
        Internal helper function that receives a list of 5 cards and returns the hand type,
        the 5 cards that make it up, and the kicker cards (if necessary).
        Cards must be sorted from high to low by rank.
        """
        # Ensure it's exactly 5 cards
        if len(cards) != 5:
            raise ValueError("The _get_hand_type_and_cards function expects a list of 5 cards.")

        # Helper information: count ranks and suits
        rank_counts = Counter(c.rank for c in cards)
        suit_counts = Counter(c.suit for c in cards)
        sorted_ranks_values = sorted([c.rank.value for c in cards], reverse=True) # Sorted ranks
        
        # Identify straight
        is_straight = self._check_straight(sorted_ranks_values)
        
        # Identify flush
        is_flush = len(suit_counts) == 1

        # Checks from high to low (to find the best hand)
        
        # 1. Royal Flush
        if is_straight and is_flush and \
           sorted_ranks_values == [Card.Rank.ACE.value, Card.Rank.KING.value, Card.Rank.QUEEN.value, Card.Rank.JACK.value, Card.Rank.TEN.value]:
            return HandRank.ROYAL_FLUSH, cards, []

        # 2. Straight Flush
        if is_straight and is_flush:
            return HandRank.STRAIGHT_FLUSH, cards, []

        # 3. Four of a Kind
        for rank, count in rank_counts.items():
            if count == 4:
                quad_cards = [c for c in cards if c.rank == rank]
                kicker = [c for c in cards if c.rank != rank] # Single kicker card
                return HandRank.FOUR_OF_A_KIND, quad_cards + sorted(kicker, key=lambda c: c.rank.value, reverse=True)[:1], sorted(kicker, key=lambda c: c.rank.value, reverse=True)[1:] # Kickers
        
        # 4. Full House
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

        # 5. Flush
        if is_flush:
            return HandRank.FLUSH, cards, []

        # 6. Straight
        if is_straight:
            return HandRank.STRAIGHT, cards, []

        # 7. Three of a Kind
        for rank, count in rank_counts.items():
            if count == 3:
                trips_cards = [c for c in cards if c.rank == rank]
                kickers = [c for c in cards if c.rank != rank]
                return HandRank.THREE_OF_A_KIND, trips_cards + sorted(kickers, key=lambda c: c.rank.value, reverse=True)[:2], sorted(kickers, key=lambda c: c.rank.value, reverse=True)[2:]

        # 8. Two Pair
        pairs = [rank for rank, count in rank_counts.items() if count == 2]
        if len(pairs) == 2:
            pair_cards = [c for c in cards if c.rank in pairs]
            kicker = [c for c in cards if c.rank not in pairs]
            return HandRank.TWO_PAIR, sorted(pair_cards, key=lambda c: c.rank.value, reverse=True) + sorted(kicker, key=lambda c: c.rank.value, reverse=True)[:1], sorted(kicker, key=lambda c: c.rank.value, reverse=True)[1:]

        # 9. Pair
        if len(pairs) == 1:
            pair_cards = [c for c in cards if c.rank == pairs[0]]
            kickers = [c for c in cards if c.rank != pairs[0]]
            return HandRank.PAIR, sorted(pair_cards, key=lambda c: c.rank.value, reverse=True) + sorted(kickers, key=lambda c: c.rank.value, reverse=True)[:3], sorted(kickers, key=lambda c: c.rank.value, reverse=True)[3:]

        # 10. High Card
        return HandRank.HIGH_CARD, cards[:5], cards[5:] # All 5 cards are the hand, empty kickers


    def _check_straight(self, sorted_rank_values: List[int]) -> bool:
        """
        Helper function: Checks if a sequence (straight) exists in 5 card ranks.
        Cards must be sorted in descending order.
        Also handles the A-5 straight case.
        """
        if len(sorted_rank_values) < 5:
            return False

        # Check for regular straight (K, Q, J, 10, 9)
        is_regular_straight = True
        for i in range(len(sorted_rank_values) - 1):
            if sorted_rank_values[i] - 1 != sorted_rank_values[i+1]:
                is_regular_straight = False
                break
        if is_regular_straight:
            return True

        # Check for A-5 straight (5, 4, 3, 2, A)
        # This means the ranks are 5,4,3,2,1 (where 1 is low Ace)
        # The sorted ranks will be: [5, 4, 3, 2, 14] for A,5,4,3,2.
        # Therefore, this set needs to be checked separately.
        if set(sorted_rank_values) == {Card.Rank.ACE.value, Card.Rank.FIVE.value, Card.Rank.FOUR.value, Card.Rank.THREE.value, Card.Rank.TWO.value}:
             return True # This is an A-5 straight
        
        return False


    def compare_hands(self, hand1_info: Tuple[HandRank, List[Card], List[Card]], hand2_info: Tuple[HandRank, List[Card], List[Card]]) -> int:
        """
        Compares two hands evaluated by evaluate_hand.

        :param hand1_info: Tuple of hand 1 information (HandRank, cards, kickers).
        :param hand2_info: Tuple of hand 2 information (HandRank, cards, kickers).
        :return: 1 if hand 1 wins, -1 if hand 2 wins, 0 if it's a tie.
        """
        rank1, cards1, kickers1 = hand1_info
        rank2, cards2, kickers2 = hand2_info

        # Step 1: Compare by hand rank
        if rank1.value > rank2.value:
            return 1
        if rank2.value > rank1.value:
            return -1

        # Step 2: If ranks are equal, compare by the cards making up the hand (and kickers)
        # Ensure that cards1 and cards2 are sorted from high to low.
        # They should be from _get_hand_type_and_cards

        # Compare the cards making up the hand
        for i in range(min(len(cards1), len(cards2))):
            if cards1[i].rank.value > cards2[i].rank.value:
                return 1
            if cards2[i].rank.value > cards1[i].rank.value:
                return -1

        # Compare kickers, if any (only if the hand itself is completely identical)
        # Ensure that kickers1 and kickers2 are also sorted.
        # Note: Ensure that the way kickers are returned in _get_hand_type_and_cards is correct for each case.
        for i in range(min(len(kickers1), len(kickers2))):
            if kickers1[i].rank.value > kickers2[i].rank.value:
                return 1
            if kickers2[i].rank.value > kickers1[i].rank.value:
                return -1
        
        # If everything is equal (including kickers), then it's a tie.
        return 0

    def __str__(self) -> str:
        return "Poker Hand Evaluator"

    def __repr__(self) -> str:
        return "HandEvaluator()"
