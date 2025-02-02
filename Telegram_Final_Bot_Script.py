import os
import signal
import sys
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("Please set the BOT_TOKEN environment variable in the .env file.")

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

user_warnings = {}

async def welcome_new_members(update: Update, context: CallbackContext):
    try:
        print("Received a new chat members event!")  # Debugging
        if update.message and update.message.new_chat_members:
            for new_member in update.message.new_chat_members:
                print(f"New Member: {new_member.first_name}")
                join_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                welcome_message = (
                    f"Hello {new_member.first_name}! 👋\n\n"
                    f"Welcome to *Telugu Friends*!\n\n"
                    f"{GROUP_RULES}\n"
                    f"*Join Time*: {join_time}\n\n"
                    "Thank you for joining! 😊"
                )
                await update.message.reply_text(welcome_message, parse_mode='Markdown')
    except Exception as e:
        print(f"Error in welcome_new_members: {e}")

async def send_rules(update: Update, context: CallbackContext):
    try:
        await update.message.reply_text(GROUP_RULES, parse_mode='Markdown')
    except Exception as e:
        print(f"Error in send_rules: {e}")

async def tag_admins(update: Update, context: CallbackContext):
    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        admin_tags = " ".join([f"@{admin.user.username}" for admin in admins if admin.user.username])
        if admin_tags:
            await update.message.reply_text(f"Admins: {admin_tags}")
        else:
            await update.message.reply_text("No admins have usernames available to mention.")
    except Exception as e:
        print(f"Error in tag_admins: {e}")

async def warn_member(update: Update, context: CallbackContext):
    try:
        admins = [admin.user.id for admin in await context.bot.get_chat_administrators(update.effective_chat.id)]
        if update.effective_user.id not in admins:
            await update.message.reply_text("You are not authorized to use this command.")
            return
        if not update.message.reply_to_message:
            await update.message.reply_text("Please reply to a message to warn the user.")
            return
        user_to_warn = update.message.reply_to_message.from_user
        user_id = user_to_warn.id
        user_warnings[user_id] = user_warnings.get(user_id, 0) + 1
        await update.message.reply_text(
            f"⚠️ {user_to_warn.first_name} has been warned. Warnings: {user_warnings[user_id]}/3"
        )
        if user_warnings[user_id] >= 3:
            await context.bot.ban_chat_member(update.effective_chat.id, user_id)
            await update.message.reply_text(f"🚫 {user_to_warn.first_name} has been banned.")
            del user_warnings[user_id]
    except Exception as e:
        print(f"Error in warn_member: {e}")

def signal_handler(sig, frame):
    print("Bot is shutting down...")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    application = Application.builder().token(BOT_TOKEN).build()
    
    # Fix: Only listen to new member events
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    application.add_handler(CommandHandler("rules", send_rules))
    application.add_handler(CommandHandler("admins", tag_admins))
    application.add_handler(CommandHandler("warn", warn_member))
    
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
