from telegram.ext import Application
import logging
from bot.handlers import RummyBotHandlers
from config import BOT_TOKEN

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Initialize handlers
    rummy_handlers = RummyBotHandlers()
    
    # Get conversation handler
    conv_handler = rummy_handlers.get_conversation_handler()
    
    # Add handlers
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", rummy_handlers.help_command))
    application.add_handler(CommandHandler("start", rummy_handlers.start))
    
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
