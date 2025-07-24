from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from .constants import SUITS, RANKS

def validate_card(card: str) -> bool:
    """Check if a single card string is valid."""
    if len(card) < 2:
        return False
    
    # Extract rank and suit
    rank = card[:-1]
    suit = card[-1]
    
    return rank in RANKS and suit in SUITS

def validate_cards(cards: List[str]) -> bool:
    """Validate a list of cards."""
    return all(validate_card(card) for card in cards)

# ... [rest of your existing utils functions] ...
