import os
import signal
import sys
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Get the bot token from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Check if the bot token is set
if not BOT_TOKEN:
    raise ValueError("Please set the BOT_TOKEN environment variable in the .env file.")

# Group rules
GROUP_RULES = """
Please follow these rules:
1. Be respectful to everyone.
2. No spamming or self-promotion.
3. No abusive language.
4. No porn or immoral content.
5. No DMs allowed.
6. No ban reasons will be provided.
7. Channels are not allowed in VC.
"""

# Function to handle new members joining the group
async def welcome_new_members(update: Update, context: CallbackContext):
    for new_member in update.message.new_chat_members:
        # Get the current date and time
        join_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Welcome message with rules and join time
        welcome_message = (
            f"Hello {new_member.first_name}! 👋\n\n"
            f"Welcome to *Telugu Friends*!\n\n"
            f"{GROUP_RULES}\n"
            f"*Join Time*: {join_time}\n\n"
            "Thank you for joining! 😊"
        )
        
        # Send the welcome message
        await update.message.reply_text(welcome_message, parse_mode='Markdown')

# Function to handle the /rules command
async def send_rules(update: Update, context: CallbackContext):
    await update.message.reply_text(GROUP_RULES, parse_mode='Markdown')

# Function to handle any other messages (optional)
async def handle_message(update: Update, context: CallbackContext):
    # You can add additional message handling logic here if needed
    pass

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    print("Bot is shutting down...")
    sys.exit(0)

def main():
    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create an Application object with your bot token
    application = Application.builder().token(BOT_TOKEN).build()

    # Register the welcome_new_members function to handle new members
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))

    # Register the /rules command
    application.add_handler(CommandHandler("rules", send_rules))

    # Register a handler for regular messages (optional)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
