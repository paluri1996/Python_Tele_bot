import os
import signal
import sys
from dotenv import load_dotenv
from telegram import Update, ChatMemberUpdated, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, ChatMemberHandler, filters, CallbackContext
from datetime import datetime

# Load environment variables
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
    """ Welcomes all members when they join the group. """
    try:
        if update.message and update.message.new_chat_members:
            for new_member in update.message.new_chat_members:
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
    """ Sends the group rules when the /rules command is used. """
    try:
        await update.message.reply_text(GROUP_RULES, parse_mode='Markdown')
    except Exception as e:
        print(f"Error in send_rules: {e}")

async def tag_admins(update: Update, context: CallbackContext):
    """ Tags all admins when /admins is used. """
    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        admin_tags = " ".join([f"@{admin.user.username}" for admin in admins if admin.user.username])
        await update.message.reply_text(f"Admins: {admin_tags}" if admin_tags else "No admins available to mention.")
    except Exception as e:
        print(f"Error in tag_admins: {e}")

async def warn_member(update: Update, context: CallbackContext):
    """ Warns a member and bans them if they reach 3 warnings. """
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

async def handle_voice_chat(update: Update, context: CallbackContext):
    """ Removes channel users from VC and mutes users who are not in the group. """
    try:
        chat_member: ChatMemberUpdated = update.chat_member

        # Get admin list
        admins = [admin.user.id for admin in await context.bot.get_chat_administrators(update.effective_chat.id)]

        # If a channel joins VC, remove it
        if chat_member.new_chat_member.status in [ChatMember.OWNER, ChatMember.ADMINISTRATOR] and chat_member.new_chat_member.user.is_bot:
            if chat_member.new_chat_member.user.id not in admins:
                await context.bot.ban_chat_member(update.effective_chat.id, chat_member.new_chat_member.user.id)
                print(f"Removed channel user {chat_member.new_chat_member.user.first_name} from VC.")

        # If a user joins VC but is not a group member, mute them
        elif chat_member.new_chat_member.status == ChatMember.MEMBER:
            user_id = chat_member.new_chat_member.user.id
            member_status = await context.bot.get_chat_member(update.effective_chat.id, user_id)
            if member_status.status not in ["member", "administrator", "creator"]:
                await context.bot.restrict_chat_member(
                    update.effective_chat.id, user_id, permissions={"can_send_messages": False}
                )
                print(f"Muted {chat_member.new_chat_member.user.first_name} for not being in the group.")
    except Exception as e:
        print(f"Error in handle_voice_chat: {e}")

def signal_handler(sig, frame):
    """ Handles bot shutdown gracefully. """
    print("Bot is shutting down...")
    sys.exit(0)

def main():
    """ Main bot function to register handlers and start polling. """
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    application = Application.builder().token(BOT_TOKEN).build()
    
    # Welcome members who join at any time
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    
    # Command Handlers
    application.add_handler(CommandHandler("rules", send_rules))
    application.add_handler(CommandHandler("admins", tag_admins))
    application.add_handler(CommandHandler("warn", warn_member))

    # Voice Chat Handlers (FIXED)
    application.add_handler(MessageHandler(filters.StatusUpdate.VIDEO_CHAT_STARTED | filters.StatusUpdate.VIDEO_CHAT_ENDED, handle_voice_chat))
    application.add_handler(ChatMemberHandler(handle_voice_chat))  # FIXED MEMBER STATUS HANDLING

    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
