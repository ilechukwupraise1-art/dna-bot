from flask import Flask
import threading
import os, time, asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive!"
def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get('BOT_TOKEN') or os.environ.get('TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))

user_messages=defaultdict(list)
warnings={}
muted_users={}
banned_users=set()
blacklist=set()
SPAM_LIMIT=5
SPAM_TIME=10

async def check_spam(uid):
    if uid in banned_users or uid in muted_users:
        return True
    now=time.time()
    user_messages[uid]=[t for t in user_messages[uid] if now-t < SPAM_TIME]
    user_messages[uid].append(now)
    return len(user_messages[uid])>=SPAM_LIMIT

async def is_admin(u,c):
    if u.id == ADMIN_ID:
        return True
    try:
        m=await c.bot.get_chat_member(c.effective_chat.id, u.id)
        return m.status in ['administrator','creator']
    except:
        return False

# --- KEEP YOUR OTHER FUNCTIONS FROM OLD FILE BELOW THIS LINE ---
# Paste your original commands (start, ban, mute etc) here
# For now I add a simple start to test deploy

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("DNA Bot is LIVE and working!")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("unban", unban))
    application.add_handler(CommandHandler("mute", mute))
    application.add_handler(CommandHandler("unmute", unmute))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("blacklist", add_blacklist))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
