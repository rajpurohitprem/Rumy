from typing import List, Dict, Tuple, Optional
from .constants import SUITS, RANKS

def parse_cards(card_str: str) -> List[str]:
    """Parse space-separated card string into list of cards."""
    return card_str.upper().split()

def validate_card(card: str) -> bool:
    """Check if a card string is valid."""
    if len(card) < 2:
        return False
    
    # Extract rank and suit
    rank = card[:-1]
    suit = card[-1]
    
    return rank in RANKS and suit in SUITS

def validate_cards(cards: List[str]) -> bool:
    """Validate a list of cards."""
    return all(validate_card(card) for card in cards)

def calculate_card_value(card: str, joker: Optional[str] = None) -> Tuple[int, int]:
    """
    Calculate the value of a card for sorting purposes.
    Returns (is_joker, rank_value, suit_value)
    """
    rank = card[:-1]
    suit = card[-1]
    
    # Check if this card is the joker
    is_joker = (card == joker)
    
    rank_value = RANKS.index(rank) if rank in RANKS else -1
    suit_value = SUITS.index(suit) if suit in SUITS else -1
    
    return (is_joker, rank_value, suit_value)

def sort_cards(cards: List[str], joker: Optional[str] = None) -> List[str]:
    """Sort cards by suit and rank, with jokers first."""
    return sorted(
        cards,
        key=lambda card: calculate_card_value(card, joker),
        reverse=True
    )

def cards_to_str(cards: List[str]) -> str:
    """Convert list of cards to space-separated string."""
    return " ".join(cards)
