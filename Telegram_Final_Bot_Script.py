import logging
from telegram import Update, ChatMember
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ChatMemberHandler,
    ContextTypes, filters
)
import google.generativeai as genai

# Bot Identity
BOT_NAME = "Honey"
BOT_OWNER_USERNAME = "@Dad_Dom"

# Replace with your real keys
TELEGRAM_BOT_TOKEN = "8013642341:AAE9yPr3BFxYGCOyh2uvIqaFmECUWzjjEZw"
GEMINI_API_KEY = "AIzaSyCBuhgiYDbKEsmxuaJxOuLEY1DVdsyDWZg"

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# Logger
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- Bot Commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Hey, I'm {BOT_NAME}! Your smart AI group assistant.\nOwner: {BOT_OWNER_USERNAME}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"*{BOT_NAME} Commands:*\n"
        "/start - Start the bot\n"
        "/help - Show this message\n"
        "/about - Info about Dom\n"
        "/info - Get your user info\n"
        "/settings - Bot settings\n"
        "/tagadmins - Tag all admins\n"
        "/rules - Group rules",
        parse_mode="Markdown"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"I'm {BOT_NAME}, an AI chatbot built for group management and smart replies. 🤖\nOwner: {BOT_OWNER_USERNAME}")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await update.message.reply_text(
        f"*User Info:*\n"
        f"👤 Name: {user.full_name}\n"
        f"🆔 User ID: {user.id}\n"
        f"📛 Username: @{user.username if user.username else 'Not set'}",
        parse_mode="Markdown"
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚙️ Settings panel is under construction...")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📜 *Group Rules:*\n"
        "👉 No Channels Allowed\n"
        "👉 No Porn & immoral stuff\n"
        "👉 No vulgar language\n"
        "👉 No pm's & dm's allowed\n"
        "👉 No Fights\n"
        "👉 Dots, single letters, and links are not allowed.",
        parse_mode="Markdown"
    )

async def tag_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != BOT_OWNER_USERNAME.lstrip('@'):
        await update.message.reply_text("🚫 Only the bot owner can use this command.")
        return

    admins = await context.bot.get_chat_administrators(update.effective_chat.id)
    tags = "👮‍♂️ Admins:\n" + "\n".join([f"@{admin.user.username}" for admin in admins if admin.user.username])
    await update.message.reply_text(tags)

# --- AI Chat Handler ---
async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    text = message.text.lower()
    chat_type = update.effective_chat.type

    is_private = chat_type == "private"
    is_mentioned = "honey" in text
    is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id

    if not (is_private or is_mentioned or is_reply_to_bot):
        return

    user_input = text.strip()

    if "your name" in user_input or "who are you" in user_input:
        await message.reply_text(f"My name is {BOT_NAME}, your group assistant 🤖")
        return
    if "who made you" in user_input or "who created you" in user_input:
        await message.reply_text(f"I was created by {BOT_OWNER_USERNAME} 💡")
        return
    if "who is the play boy in telegram" in user_input:
        await message.reply_text("Dubai Seenu is the Play Boy in Telegram")
        return
    if "who is the hero in this group" in user_input:
        await message.reply_text("Gaali Seenu is the Hero in the group")
        return
    if "who are the owners of the group" in user_input:
        await message.reply_text("Gaali Seenu , Bunk Seenu , Dubai Seenu are the Owners")
        return

    try:
        response = model.generate_content(user_input)
        await message.reply_text(response.text)
    except Exception as e:
        logging.error(f"AI error: {e}")
        await message.reply_text("⚠️ Oops! I had trouble generating a response.")

# --- Welcome/Goodbye ---
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        if not user.username and user.first_name == "":
            await update.effective_chat.ban_member(user.id)
            await update.message.reply_text("❌ Channels are not allowed!")
        else:
            await update.message.reply_text(f"👋 Welcome, {user.full_name}!")

async def goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.left_chat_member:
        await update.message.reply_text(f"👋 Goodbye, {update.message.left_chat_member.full_name}!")

# --- VC / Channel Join Detection ---
async def monitor_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new: ChatMember = update.chat_member.new_chat_member
    user = update.chat_member.from_user
    if new.status == "member" and user.username is None and user.first_name == "":
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await context.bot.send_message(update.effective_chat.id, "❌ Channel accounts are not allowed!")

# --- Main Runner ---
def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(CommandHandler("settings", settings))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("tagadmins", tag_admins))

    # Welcome/Leave
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye))

    # AI Chat
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat))

    # Monitor channel joins / VC joins
    app.add_handler(ChatMemberHandler(monitor_chat_member, ChatMemberHandler.CHAT_MEMBER))

    logging.info("🤖 Dom is up and running!")
    app.run_polling()

if __name__ == "__main__":
    main()
