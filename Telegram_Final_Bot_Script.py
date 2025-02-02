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

# Dictionary to store warnings for each user
user_warnings = {}

# Function to handle new members joining the group
async def welcome_new_members(update: Update, context: CallbackContext):
    try:
        print("New member joined!")  # Debug statement
        for new_member in update.message.new_chat_members:
            print(f"Welcoming {new_member.first_name}")  # Debug statement
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
    except Exception as e:
        print(f"Error in welcome_new_members: {e}")  # Debug statement

# Function to handle the /rules command
async def send_rules(update: Update, context: CallbackContext):
    try:
        print("/rules command received")  # Debug statement
        await update.message.reply_text(GROUP_RULES, parse_mode='Markdown')
    except Exception as e:
        print(f"Error in send_rules: {e}")  # Debug statement

# Function to handle the @admins command
async def tag_admins(update: Update, context: CallbackContext):
    try:
        print("@admins command received")  # Debug statement
        # Get the list of admins in the group
        admins = await update.effective_chat.get_administrators()
        admin_tags = " ".join([f"@{admin.user.username}" for admin in admins if admin.user.username])
        
        # Send the message tagging all admins
        await update.message.reply_text(f"Admins: {admin_tags}")
    except Exception as e:
        print(f"Error in tag_admins: {e}")  # Debug statement

# Function to handle the /warn command (admin-only)
async def warn_member(update: Update, context: CallbackContext):
    try:
        print("/warn command received")  # Debug statement
        # Check if the user is an admin
        if update.effective_user.id not in [admin.user.id for admin in await update.effective_chat.get_administrators()]:
            await update.message.reply_text("You are not authorized to use this command.")
            return

        # Get the user to warn
        if not update.message.reply_to_message:
            await update.message.reply_text("Please reply to a message to warn the user.")
            return

        user_to_warn = update.message.reply_to_message.from_user
        user_id = user_to_warn.id

        # Increment the warning count
        user_warnings[user_id] = user_warnings.get(user_id, 0) + 1

        # Send a warning message
        await update.message.reply_text(
            f"⚠️ {user_to_warn.first_name} has been warned. "
            f"Warnings: {user_warnings[user_id]}/3"
        )

        # Ban the user after 3 warnings
        if user_warnings[user_id] >= 3:
            await context.bot.ban_chat_member(update.effective_chat.id, user_id)
            await update.message.reply_text(f"🚫 {user_to_warn.first_name} has been banned for receiving 3 warnings.")
            del user_warnings[user_id]  # Reset warnings after banning
    except Exception as e:
        print(f"Error in warn_member: {e}")  # Debug statement

# Function to handle the /ban command (admin-only)
async def ban_member(update: Update, context: CallbackContext):
    try:
        print("/ban command received")  # Debug statement
        # Check if the user is an admin
        if update.effective_user.id not in [admin.user.id for admin in await update.effective_chat.get_administrators()]:
            await update.message.reply_text("You are not authorized to use this command.")
            return

        # Get the user to ban
        if not update.message.reply_to_message:
            await update.message.reply_text("Please reply to a message to ban the user.")
            return

        user_to_ban = update.message.reply_to_message.from_user
        await context.bot.ban_chat_member(update.effective_chat.id, user_to_ban.id)
        await update.message.reply_text(f"🚫 {user_to_ban.first_name} has been banned.")
    except Exception as e:
        print(f"Error in ban_member: {e}")  # Debug statement

# Function to handle the /unban command (admin-only)
async def unban_user(update: Update, context: CallbackContext):
    try:
        print("/unban command received")  # Debug statement
        # Check if the user is an admin
        if update.effective_user.id not in [admin.user.id for admin in await update.effective_chat.get_administrators()]:
            await update.message.reply_text("You are not authorized to use this command.")
            return

        # Get the user to unban
        if not context.args:
            await update.message.reply_text("Please provide the username or ID of the user to unban.")
            return

        user_to_unban = context.args[0]
        await context.bot.unban_chat_member(update.effective_chat.id, user_to_unban)
        await update.message.reply_text(f"✅ {user_to_unban} has been unbanned.")
    except Exception as e:
        print(f"Error in unban_user: {e}")  # Debug statement

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

    # Register the @admins command
    application.add_handler(CommandHandler("admins", tag_admins))

    # Register the /warn command (admin-only)
    application.add_handler(CommandHandler("warn", warn_member))

    # Register the /ban command (admin-only)
    application.add_handler(CommandHandler("ban", ban_member))

    # Register the /unban command (admin-only)
    application.add_handler(CommandHandler("unban", unban_user))

    # Register a handler for regular messages (optional)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
