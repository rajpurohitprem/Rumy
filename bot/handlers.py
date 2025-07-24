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
from .utils import parse_cards, validate_cards, cards_to_str, sort_cards
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
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler. Initializes a new game."""
        user_id = update.message.from_user.id
        
        # Initialize or reset game state for this user
        if user_id in self.user_sessions:
            self.user_sessions[user_id].reset()
        else:
            self.user_sessions[user_id] = GameState()
        
        await update.message.reply_text(
            "🃏 Welcome to Rummy AI Assistant!\n\n"
            "Please enter your initial 13 cards separated by spaces (e.g., '7C 8C 9C KH QH JH 3S 3D 3C 5S 6S 2D JC')"
        )
        
        return WAITING_FOR_HAND
    
    async def receive_hand(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive and validate the user's initial hand."""
        user_id = update.message.from_user.id
        hand_text = update.message.text
        
        try:
            cards = parse_cards(hand_text)
            if len(cards) != 13:
                await update.message.reply_text("Please enter exactly 13 cards. Try again.")
                return WAITING_FOR_HAND
            
            if not validate_cards(cards):
                await update.message.reply_text("Invalid card format. Use format like '7C' for 7 of Clubs. Try again.")
                return WAITING_FOR_HAND
            
            # Store the hand and ask for joker
            self.user_sessions[user_id].hand = cards
            
            await update.message.reply_text(
                "♠️ Got your hand. Now please enter the joker card (e.g., '7D'):"
            )
            
            return WAITING_FOR_JOKER
        except Exception as e:
            await update.message.reply_text(f"Error processing your hand: {e}. Please try again.")
            return WAITING_FOR_HAND
    
    async def receive_joker(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive and validate the joker card."""
        user_id = update.message.from_user.id
        joker_text = update.message.text.strip().upper()
        
        try:
            if not validate_card(joker_text):
                await update.message.reply_text("Invalid joker card format. Use format like '7D'. Try again.")
                return WAITING_FOR_JOKER
            
            # Store the joker
            self.user_sessions[user_id].joker = joker_text
            
            # Suggest initial action (Play or Drop)
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
    
    async def handle_play_or_drop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user's decision to play or drop."""
        user_id = update.message.from_user.id
        decision = update.message.text
        
        if decision not in ["Play", "Drop"]:
            await update.message.reply_text("Please choose either 'Play' or 'Drop'.")
            return SHOWING_SUGGESTION
        
        if decision == "Drop":
            await update.message.reply_text(
                "You chose to Drop. Game ended.\n\n"
                "Type /start to begin a new game."
            )
            return ConversationHandler.END
        else:
            # User chose to Play, continue with game setup
            await update.message.reply_text(
                "You chose to Play. Let's set up the game.\n\n"
                "Please enter the current discard pile (open deck) cards separated by spaces "
                "(enter 'none' if empty):"
            )
            return WAITING_FOR_DISCARD_PILE
    
    async def receive_discard_pile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive and validate the discard pile."""
        user_id = update.message.from_user.id
        discard_text = update.message.text.strip().lower()
        
        try:
            if discard_text == "none":
                cards = []
            else:
                cards = parse_cards(discard_text)
                if not validate_cards(cards):
                    await update.message.reply_text("Invalid card format. Use format like '7C'. Try again.")
                    return WAITING_FOR_DISCARD_PILE
            
            self.user_sessions[user_id].discard_pile = cards
            
            await update.message.reply_text(
                "Now please enter any cards your opponent has picked from the open deck "
                "(separated by spaces, enter 'none' if none):"
            )
            
            return WAITING_FOR_OPPONENT_PICKS
        except Exception as e:
            await update.message.reply_text(f"Error processing discard pile: {e}. Please try again.")
            return WAITING_FOR_DISCARD_PILE
    
    async def receive_opponent_picks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive opponent's picks from open deck."""
        user_id = update.message.from_user.id
        picks_text = update.message.text.strip().lower()
        
        try:
            if picks_text == "none":
                cards = []
            else:
                cards = parse_cards(picks_text)
                if not validate_cards(cards):
                    await update.message.reply_text("Invalid card format. Use format like '7C'. Try again.")
                    return WAITING_FOR_OPPONENT_PICKS
            
            self.user_sessions[user_id].opponent_picks = cards
            
            await update.message.reply_text(
                "Now please enter any cards your opponent has discarded "
                "(separated by spaces, enter 'none' if none):"
            )
            
            return WAITING_FOR_OPPONENT_DISCARDS
        except Exception as e:
            await update.message.reply_text(f"Error processing opponent picks: {e}. Please try again.")
            return WAITING_FOR_OPPONENT_PICKS
    
    async def receive_opponent_discards(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive opponent's discards."""
        user_id = update.message.from_user.id
        discards_text = update.message.text.strip().lower()
        
        try:
            if discards_text == "none":
                cards = []
            else:
                cards = parse_cards(discards_text)
                if not validate_cards(cards):
                    await update.message.reply_text("Invalid card format. Use format like '7C'. Try again.")
                    return WAITING_FOR_OPPONENT_DISCARDS
            
            self.user_sessions[user_id].opponent_discards = cards
            
            await update.message.reply_text(
                "Finally, please enter the current open card (the face-up card on the discard pile, "
                "or 'none' if the discard pile is empty):"
            )
            
            return WAITING_FOR_OPEN_CARD
        except Exception as e:
            await update.message.reply_text(f"Error processing opponent discards: {e}. Please try again.")
            return WAITING_FOR_OPPONENT_DISCARDS
    
    async def receive_open_card(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Receive the current open card."""
        user_id = update.message.from_user.id
        open_card_text = update.message.text.strip().lower()
        
        try:
            if open_card_text == "none":
                card = None
            else:
                card = open_card_text.upper()
                if not validate_card(card):
                    await update.message.reply_text("Invalid card format. Use format like '7C'. Try again.")
                    return WAITING_FOR_OPEN_CARD
            
            state = self.user_sessions[user_id]
            state.open_card = card
            
            # Now we have all info to make suggestions
            pick_source = self.ai.suggest_pick_source(
                hand=state.hand,
                joker=state.joker,
                open_card=state.open_card,
                discard_pile=state.discard_pile,
                opponent_picks=state.opponent_picks,
                opponent_discards=state.opponent_discards
            )
            
            # Check if we should set a trap
            trap_card = self.ai.suggest_trap_card(
                hand=state.hand,
                joker=state.joker,
                opponent_picks=state.opponent_picks,
                opponent_discards=state.opponent_discards
            )
            
            if trap_card:
                state.trap_activated = True
                discard_suggestion = trap_card
                trap_msg = f"\n\n🎣 Trap activated! Discarding {trap_card} as bait."
            else:
                state.trap_activated = False
                discard_suggestion = self.ai.suggest_discard(
                    hand=state.hand,
                    joker=state.joker,
                    picked_card=None,  # No picked card yet
                    discard_pile=state.discard_pile,
                    opponent_picks=state.opponent_picks,
                    opponent_discards=state.opponent_discards
                )
                trap_msg = ""
            
            await update.message.reply_text(
                f"🃏 Game Setup Complete!\n\n"
                f"Current hand: {cards_to_str(sort_cards(state.hand, state.joker))}\n"
                f"Joker: {state.joker}\n"
                f"Open card: {state.open_card if state.open_card else 'None'}\n\n"
                f"AI Suggestion:\n"
                f"1. Pick from: {pick_source}\n"
                f"2. Discard: {discard_suggestion}"
                f"{trap_msg}\n\n"
                f"Select where to pick from:",
                reply_markup=get_pick_source_keyboard()
            )
            
            # Store the suggested discard for later
            state.suggested_discard = discard_suggestion
            
            return GAME_ACTIVE
        except Exception as e:
            await update.message.reply_text(f"Error processing open card: {e}. Please try again.")
            return WAITING_FOR_OPEN_CARD
    
    async def handle_pick_source(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user's selection of pick source."""
        user_id = update.message.from_user.id
        pick_source = update.message.text
        state = self.user_sessions[user_id]
        
        if pick_source not in ["Open Deck", "Closed Deck"]:
            await update.message.reply_text("Please select either 'Open Deck' or 'Closed Deck'.")
            return GAME_ACTIVE
        
        # Update game state
        if pick_source == "Open Deck" and state.open_card:
            state.picked_card = state.open_card
            state.hand.append(state.open_card)
            state.open_card = None  # Picked card is removed from open deck
        else:
            # For closed deck, we simulate a random card (in real game, user would know)
            # Here we just use the suggested discard as a placeholder
            state.picked_card = "Unknown Card (from closed deck)"
        
        # Show discard options
        await update.message.reply_text(
            f"You picked from {pick_source.lower()}.\n"
            f"Picked card: {state.picked_card}\n\n"
            "Now select a card to discard:",
            reply_markup=get_discard_keyboard(sort_cards(state.hand, state.joker))
        )
        
        return GAME_ACTIVE
    
    async def handle_discard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user's discard selection."""
        user_id = update.message.from_user.id
        discard_card = update.message.text.strip().upper()
        state = self.user_sessions[user_id]
        
        try:
            if not validate_card(discard_card) or discard_card not in state.hand:
                await update.message.reply_text("Invalid card selection. Please choose from your hand.")
                return GAME_ACTIVE
            
            # Update game state
            state.hand.remove(discard_card)
            state.discard_pile.append(discard_card)
            state.open_card = discard_card  # New open card is the discarded one
            
            # Check if trap was successful (simplified logic)
            trap_result = ""
            if state.trap_activated and discard_card == state.suggested_discard:
                # In a real game, we'd wait to see if opponent picks it
                # Here we just simulate some probability
                if random.random() > 0.7:  # 30% chance trap works
                    trap_result = "\n\n🎣 The opponent fell for your trap!"
                else:
                    trap_result = "\n\n🎣 The opponent ignored your trap."
            
            await update.message.reply_text(
                f"✅ You discarded: {discard_card}\n"
                f"New open card: {state.open_card}\n"
                f"Your hand: {cards_to_str(sort_cards(state.hand, state.joker))}"
                f"{trap_result}\n\n"
                "What would you like to do next?\n"
                "1. Continue playing (enter anything)\n"
                "2. /start - New game\n"
                "3. /cancel - End current game"
            )
            
            # Reset for next turn
            state.picked_card = None
            state.trap_activated = False
            
            return GAME_ACTIVE
        except Exception as e:
            await update.message.reply_text(f"Error processing discard: {e}. Please try again.")
            return GAME_ACTIVE
    
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the current game."""
        user_id = update.message.from_user.id
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        await update.message.reply_text(
            "Game cancelled. Type /start to begin a new game.",
            reply_markup=None
        )
        
        return ConversationHandler.END
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a help message."""
        await update.message.reply_text(
            "🃏 Rummy AI Assistant Help:\n\n"
            "/start - Begin a new game\n"
            "/cancel - Cancel the current game\n"
            "/help - Show this help message\n\n"
            "During the game, you'll be asked to provide:\n"
            "- Your 13 starting cards\n"
            "- The joker card\n"
            "- Current discard pile\n"
            "- Opponent's picks from open deck\n"
            "- Opponent's discards\n"
            "- Current open card\n\n"
            "The AI will then suggest moves to help you win!"
        )

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
