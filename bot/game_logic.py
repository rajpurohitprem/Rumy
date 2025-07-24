from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import random
from .utils import sort_cards, validate_card, calculate_card_value

class RummyAI:
    def __init__(self):
        self.trap_history = defaultdict(int)
        self.trap_success = defaultdict(int)
        self.opponent_behavior = {
            'open_picks': defaultdict(int),
            'discards': defaultdict(int),
            'sequences_preferred': False,
            'sets_preferred': False,
        }
    
    def evaluate_hand_strength(self, hand: List[str], joker: str) -> float:
        """
        Evaluate the initial hand strength to suggest Play or Drop.
        Returns a score between 0 (weak) and 1 (strong).
        """
        if not hand or not joker:
            return 0.0
        
        # Count pure sequences (without joker)
        pure_seq_count = self._count_pure_sequences(hand)
        
        # Count potential sequences (with or without joker)
        potential_seq_count = self._count_potential_sequences(hand, joker)
        
        # Count sets
        set_count = self._count_sets(hand, joker)
        
        # Calculate score (weights can be adjusted)
        score = (pure_seq_count * 0.4) + (potential_seq_count * 0.3) + (set_count * 0.3)
        return min(score, 1.0)
    
    def _count_pure_sequences(self, hand: List[str]) -> int:
        """Count pure sequences (without jokers)."""
        # Group cards by suit
        suits = defaultdict(list)
        for card in hand:
            suits[card[-1]].append(card)
        
        # Check for sequences in each suit
        seq_count = 0
        for suit_cards in suits.values():
            sorted_cards = sorted(suit_cards, key=lambda c: RANKS.index(c[:-1]))
            seq_count += self._find_sequences_in_sorted_list(sorted_cards)
        
        return seq_count
    
    def _count_potential_sequences(self, hand: List[str], joker: str) -> int:
        """Count potential sequences (can use joker)."""
        # Similar to pure sequences but can include joker
        suits = defaultdict(list)
        for card in hand:
            suits[card[-1]].append(card)
        
        seq_count = 0
        for suit_cards in suits.values():
            sorted_cards = sorted(suit_cards, key=lambda c: RANKS.index(c[:-1]))
            seq_count += self._find_sequences_in_sorted_list(sorted_cards)
            
            # Check if adding joker could complete sequences
            # (Implementation simplified for example)
            if len(sorted_cards) >= 2:
                seq_count += 0.5  # Potential to complete with joker
        
        return seq_count
    
    def _count_sets(self, hand: List[str], joker: str) -> int:
        """Count sets of same rank."""
        rank_counts = defaultdict(int)
        for card in hand:
            rank = card[:-1]
            rank_counts[rank] += 1
        
        # Count sets (3 or 4 of same rank)
        set_count = sum(1 for count in rank_counts.values() if count >= 2)  # At least a pair
        return set_count
    
    def _find_sequences_in_sorted_list(self, cards: List[str]) -> int:
        """Helper to find sequences in a sorted list of cards of the same suit."""
        if len(cards) < 3:
            return 0
        
        sequences = 0
        current_seq = 1
        
        for i in range(1, len(cards)):
            prev_rank = RANKS.index(cards[i-1][:-1])
            curr_rank = RANKS.index(cards[i][:-1])
            
            if curr_rank == prev_rank + 1:
                current_seq += 1
                if current_seq >= 3:
                    sequences += 1
            else:
                current_seq = 1
        
        return sequences
    
    def suggest_initial_action(self, hand: List[str], joker: str) -> str:
        """Suggest whether to Play or Drop based on hand strength."""
        score = self.evaluate_hand_strength(hand, joker)
        return "Play" if score >= 0.5 else "Drop"
    
    def suggest_pick_source(
        self,
        hand: List[str],
        joker: str,
        open_card: str,
        discard_pile: List[str],
        opponent_picks: List[str],
        opponent_discards: List[str]
    ) -> str:
        """
        Suggest whether to pick from open or closed deck.
        Returns "Open Deck" or "Closed Deck".
        """
        if not open_card:
            return "Closed Deck"
        
        # Update opponent behavior
        self._update_opponent_behavior(opponent_picks, opponent_discards)
        
        # Check if open card completes a sequence or set
        if self._does_card_complete_group(hand, open_card, joker):
            return "Open Deck"
        
        # Check if opponent is likely not interested in this suit/rank
        if not self._is_card_likely_useful_to_opponent(open_card):
            return "Open Deck"
        
        # Default to closed deck for safety
        return "Closed Deck"
    
    def suggest_discard(
        self,
        hand: List[str],
        joker: str,
        picked_card: Optional[str],
        discard_pile: List[str],
        opponent_picks: List[str],
        opponent_discards: List[str]
    ) -> str:
        """
        Suggest which card to discard.
        Returns the card to discard.
        """
        # First, identify complete groups that shouldn't be broken
        protected_cards = self._identify_protected_cards(hand, joker)
        
        # Then identify cards that are least useful and not protected
        card_scores = []
        for card in hand:
            if card in protected_cards:
                card_scores.append((card, float('inf')))  # Don't discard protected cards
            else:
                usefulness = self._calculate_card_usefulness(hand, card, joker)
                danger = self._calculate_discard_danger(card, opponent_picks, opponent_discards)
                score = usefulness - danger
                card_scores.append((card, score))
        
        # The card with the lowest score is the best to discard
        card_scores.sort(key=lambda x: x[1])
        return card_scores[0][0]
    
    def _identify_protected_cards(self, hand: List[str], joker: str) -> List[str]:
        """Identify cards that are part of complete sequences or sets."""
        protected = set()
        
        # Check for sequences
        suits = defaultdict(list)
        for card in hand:
            suits[card[-1]].append(card)
        
        for suit_cards in suits.values():
            sorted_cards = sorted(suit_cards, key=lambda c: RANKS.index(c[:-1]))
            sequences = self._find_complete_sequences(sorted_cards)
            for seq in sequences:
                protected.update(seq)
        
        # Check for sets
        rank_counts = defaultdict(list)
        for card in hand:
            rank_counts[card[:-1]].append(card)
        
        for cards in rank_counts.values():
            if len(cards) >= 3:  # Complete set
                protected.update(cards)
        
        return list(protected)
    
    def _calculate_card_usefulness(self, hand: List[str], card: str, joker: str) -> float:
        """Calculate how useful a card is in the current hand."""
        # Check if card is part of a sequence
        seq_value = self._sequence_contribution(hand, card, joker)
        
        # Check if card is part of a set
        set_value = self._set_contribution(hand, card)
        
        # Check if card is joker
        joker_value = 1.0 if card == joker else 0.0
        
        return max(seq_value, set_value, joker_value)
    
    def _calculate_discard_danger(self, card: str, opponent_picks: List[str], opponent_discards: List[str]) -> float:
        """Calculate how dangerous it is to discard this card."""
        # Check if opponent has been picking similar cards
        rank = card[:-1]
        suit = card[-1]
        
        rank_danger = sum(1 for c in opponent_picks if c[:-1] == rank) / (len(opponent_picks) + 1)
        suit_danger = sum(1 for c in opponent_picks if c[-1] == suit) / (len(opponent_picks) + 1)
        
        return max(rank_danger, suit_danger)
    
    def suggest_trap_card(
        self,
        hand: List[str],
        joker: str,
        opponent_picks: List[str],
        opponent_discards: List[str]
    ) -> Optional[str]:
        """
        Suggest a card to discard as a trap, if appropriate.
        Returns None if no good trap opportunity.
        """
        # Identify cards that appear useful but aren't
        for card in hand:
            if card == joker:
                continue
                
            # Check if this card appears to complete a sequence but actually doesn't
            if self._is_false_sequence_card(hand, card, joker):
                # Check if opponent might want it
                if self._is_card_likely_useful_to_opponent(card):
                    self.trap_history[card] += 1
                    return card
        
        return None
    
    def _is_false_sequence_card(self, hand: List[str], card: str, joker: str) -> bool:
        """Check if this card appears to complete a sequence but doesn't."""
        suit = card[-1]
        rank = card[:-1]
        rank_idx = RANKS.index(rank)
        
        # Check if it appears to complete a sequence from either side
        lower_neighbor = f"{RANKS[rank_idx-1]}{suit}" if rank_idx > 0 else None
        upper_neighbor = f"{RANKS[rank_idx+1]}{suit}" if rank_idx < len(RANKS)-1 else None
        
        # Case 1: We have X and Z, this is Y - looks like it completes X Y Z
        case1 = (lower_neighbor and upper_neighbor and 
                 lower_neighbor in hand and upper_neighbor in hand)
        
        # Case 2: We have X and Y, this is Z - looks like it completes X Y Z
        case2 = (lower_neighbor and rank_idx >= 2 and 
                 lower_neighbor in hand and f"{RANKS[rank_idx-2]}{suit}" in hand)
        
        # Case 3: We have Y and Z, this is X - looks like it completes X Y Z
        case3 = (upper_neighbor and rank_idx < len(RANKS)-2 and 
                 upper_neighbor in hand and f"{RANKS[rank_idx+2]}{suit}" in hand)
        
        return case1 or case2 or case3
    
    def _is_card_likely_useful_to_opponent(self, card: str) -> bool:
        """Check if the opponent is likely to want this card."""
        rank = card[:-1]
        suit = card[-1]
        
        # Check if opponent has been collecting this rank or suit
        rank_picks = sum(1 for c in self.opponent_behavior['open_picks'] if c[:-1] == rank)
        suit_picks = sum(1 for c in self.opponent_behavior['open_picks'] if c[-1] == suit)
        
        return rank_picks > 1 or suit_picks > 2
    
    def _update_opponent_behavior(self, opponent_picks: List[str], opponent_discards: List[str]):
        """Update opponent behavior tracking based on their actions."""
        for card in opponent_picks:
            self.opponent_behavior['open_picks'][card] += 1
        
        for card in opponent_discards:
            self.opponent_behavior['discards'][card] += 1
        
        # Analyze if opponent prefers sequences or sets
        seq_clues = sum(1 for card in opponent_picks if self._is_sequence_related(card, opponent_picks))
        set_clues = sum(1 for card in opponent_picks if self._is_set_related(card, opponent_picks))
        
        if seq_clues > set_clues + 2:
            self.opponent_behavior['sequences_preferred'] = True
        elif set_clues > seq_clues + 2:
            self.opponent_behavior['sets_preferred'] = True
    
    def _is_sequence_related(self, card: str, opponent_picks: List[str]) -> bool:
        """Check if this pick suggests sequence building."""
        suit = card[-1]
        rank = card[:-1]
        rank_idx = RANKS.index(rank)
        
        # Check if neighbor cards were also picked
        lower_neighbor = f"{RANKS[rank_idx-1]}{suit}" if rank_idx > 0 else None
        upper_neighbor = f"{RANKS[rank_idx+1]}{suit}" if rank_idx < len(RANKS)-1 else None
        
        return (lower_neighbor and lower_neighbor in opponent_picks) or \
               (upper_neighbor and upper_neighbor in opponent_picks)
    
    def _is_set_related(self, card: str, opponent_picks: List[str]) -> bool:
        """Check if this pick suggests set building."""
        rank = card[:-1]
        same_rank_picks = sum(1 for c in opponent_picks if c[:-1] == rank)
        return same_rank_picks >= 2
    
    def _does_card_complete_group(self, hand: List[str], card: str, joker: str) -> bool:
        """Check if this card completes a sequence or set in our hand."""
        # Check for sequences
        suit = card[-1]
        rank = card[:-1]
        rank_idx = RANKS.index(rank)
        
        # Check for sequence completion
        lower_neighbor = f"{RANKS[rank_idx-1]}{suit}" if rank_idx > 0 else None
        upper_neighbor = f"{RANKS[rank_idx+1]}{suit}" if rank_idx < len(RANKS)-1 else None
        
        # Case 1: We have X and Y, this is Z to complete X Y Z
        if lower_neighbor and f"{RANKS[rank_idx-2]}{suit}" in hand and lower_neighbor in hand:
            return True
        
        # Case 2: We have Y and Z, this is X to complete X Y Z
        if upper_neighbor and f"{RANKS[rank_idx+2]}{suit}" in hand and upper_neighbor in hand:
            return True
        
        # Case 3: We have X and Z, this is Y to complete X Y Z
        if lower_neighbor and upper_neighbor and lower_neighbor in hand and upper_neighbor in hand:
            return True
        
        # Check for set completion
        same_rank_cards = [c for c in hand if c[:-1] == rank]
        if len(same_rank_cards) >= 2:  # Would make a set of 3+
            return True
        
        return False
