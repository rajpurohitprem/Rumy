from telegram.ext import Application, CommandHandler
import logging
from bot.handlers import RummyBotHandlers
from config import BOT_TOKEN

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()
    
    rummy_handlers = RummyBotHandlers()
    conv_handler = rummy_handlers.get_conversation_handler()
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", rummy_handlers.help_command))
    application.add_handler(CommandHandler("start", rummy_handlers.start))
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
