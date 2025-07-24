from telegram import ReplyKeyboardMarkup
from .constants import PLAY_OR_DROP, PICK_SOURCE

def get_play_or_drop_keyboard():
    return ReplyKeyboardMarkup(
        [[option] for option in PLAY_OR_DROP],
        one_time_keyboard=True,
        resize_keyboard=True
    )

def get_pick_source_keyboard():
    return ReplyKeyboardMarkup(
        [[option] for option in PICK_SOURCE],
        one_time_keyboard=True,
        resize_keyboard=True
    )

def get_discard_keyboard(cards: list):
    """Create a keyboard with the user's cards for discard selection."""
    # Split cards into rows of 4 for better display
    rows = [cards[i:i+4] for i in range(0, len(cards), 4)]
    return ReplyKeyboardMarkup(
        rows,
        one_time_keyboard=True,
        resize_keyboard=True
    )
