from telegram import Update
from telegram.ext import (
    ContextTypes, 
    ConversationHandler, 
    CommandHandler, 
    MessageHandler,
    filters
)
from typing import Dict
import re
import random
from .game_logic import RummyAI
from .keyboards import (
    get_play_or_drop_keyboard,
    get_pick_source_keyboard,
    get_discard_keyboard
)
from .utils import (
    parse_cards,
    validate_cards,
    validate_card,  # Explicitly imported
    cards_to_str,
    sort_cards
)
from .constants import (
    WAITING_FOR_HAND,
    WAITING_FOR_JOKER,
    WAITING_FOR_DISCARD_PILE,
    WAITING_FOR_OPPONENT_PICKS,
    WAITING_FOR_OPPONENT_DISCARDS,
    WAITING_FOR_OPEN_CARD,
    SHOWING_SUGGESTION,
    GAME_ACTIVE,
)

class GameState:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.hand = []
        self.joker = None
        self.discard_pile = []
        self.opponent_picks = []
        self.opponent_discards = []
        self.open_card = None
        self.picked_card = None
        self.trap_activated = False

class RummyBotHandlers:
    def __init__(self):
        self.ai = RummyAI()
        self.game_state = GameState()
        self.user_sessions = {}  # user_id: GameState
    
    async def receive_joker(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive and validate the joker card."""
        user_id = update.message.from_user.id
        joker_text = update.message.text.strip().upper()
        
        try:
            if not validate_card(joker_text):  # Now using the imported function
                await update.message.reply_text(
                    "Invalid joker card. Examples: '7D' (7♦), 'QS' (Q♠), '10H' (10♥)\n"
                    "Please try again:"
                )
                return WAITING_FOR_JOKER
            
            self.user_sessions[user_id].joker = joker_text
            hand = self.user_sessions[user_id].hand
            suggestion = self.ai.suggest_initial_action(hand, joker_text)
            
            await update.message.reply_text(
                f"Based on your hand, I suggest you: {suggestion}\n\n"
                "Would you like to Play or Drop?",
                reply_markup=get_play_or_drop_keyboard()
            )
            
            return SHOWING_SUGGESTION
        except Exception as e:
            await update.message.reply_text(f"Error processing joker: {e}. Please try again.")
            return WAITING_FOR_JOKER

    # ... [rest of your existing handler methods] ...

    def get_conversation_handler(self):
        """Return the configured conversation handler for the bot."""
        return ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                WAITING_FOR_HAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_hand)],
                WAITING_FOR_JOKER: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_joker)],
                SHOWING_SUGGESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_play_or_drop)],
                WAITING_FOR_DISCARD_PILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_discard_pile)],
                WAITING_FOR_OPPONENT_PICKS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_opponent_picks)],
                WAITING_FOR_OPPONENT_DISCARDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_opponent_discards)],
                WAITING_FOR_OPEN_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_open_card)],
                GAME_ACTIVE: [
                    MessageHandler(filters.Regex("^(Open Deck|Closed Deck)$"), self.handle_pick_source),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_discard)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.cancel)],
        )
