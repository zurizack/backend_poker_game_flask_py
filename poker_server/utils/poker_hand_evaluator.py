# poker_server/utils/poker_hand_evaluator.py

from itertools import combinations

RANK_ORDER = "23456789TJQKA"
SUITS = "♠♥♦♣"

def card_rank(card):
    return RANK_ORDER.index(card[0])

def evaluate_hand_strength(cards):
    best_score = 0
    for combo in combinations(cards, 5):
        score = score_five_card_hand(list(combo))
        best_score = max(best_score, score)
    return best_score

def score_five_card_hand(cards):
    values = sorted([card[0] for card in cards], key=RANK_ORDER.index, reverse=True)
    suits = [card[1] for card in cards]
    counts = {v: values.count(v) for v in set(values)}

    flush = len(set(suits)) == 1
    straight = is_straight(values)

    if flush and straight:
        return 800 + high_card_rank(values)
    if 4 in counts.values():
        return 700 + get_rank_value(counts, 4)
    if 3 in counts.values() and 2 in counts.values():
        return 600 + get_rank_value(counts, 3)
    if flush:
        return 500 + high_card_rank(values)
    if straight:
        return 400 + high_card_rank(values)
    if 3 in counts.values():
        return 300 + get_rank_value(counts, 3)
    if list(counts.values()).count(2) == 2:
        return 200 + get_two_pair_score(counts)
    if 2 in counts.values():
        return 100 + get_rank_value(counts, 2)

    return high_card_rank(values)

def is_straight(values):
    ixs = sorted(set(RANK_ORDER.index(v) for v in values), reverse=True)
    return any(all(ix - j in ixs for j in range(5)) for ix in ixs)

def high_card_rank(values):
    return max(RANK_ORDER.index(v) for v in values)

def get_rank_value(counts, n):
    return max(RANK_ORDER.index(v) for v, c in counts.items() if c == n)

def get_two_pair_score(counts):
    pairs = [RANK_ORDER.index(v) for v, c in counts.items() if c == 2]
    return sum(sorted(pairs, reverse=True)[:2])
