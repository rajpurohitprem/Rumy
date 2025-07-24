# Card constants
SUITS = ['H', 'D', 'C', 'S']  # Hearts, Diamonds, Clubs, Spades
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

# Game states
(
    WAITING_FOR_HAND,
    WAITING_FOR_JOKER,
    WAITING_FOR_DISCARD_PILE,
    WAITING_FOR_OPPONENT_PICKS,
    WAITING_FOR_OPPONENT_DISCARDS,
    WAITING_FOR_OPEN_CARD,
    SHOWING_SUGGESTION,
    GAME_ACTIVE,
) = range(8)

# Keyboard options
PLAY_OR_DROP = ["Play", "Drop"]
PICK_SOURCE = ["Open Deck", "Closed Deck"]
