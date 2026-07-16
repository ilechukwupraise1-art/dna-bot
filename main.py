from flask import Flask
import threading
import os, time
from collections import defaultdict
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import timedelta

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_web, daemon=True).start()

TOKEN = os.environ.get('BOT_TOKEN') or os.environ.get('TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '0'))

user_messages=defaultdict(list)
warnings={}
muted_users={}
banned_users=set()
blacklist=set()
SPAM_LIMIT=5
SPAM_TIME=10

async def is_admin(update, context):
    uid = update.effective_user.id
    if ADMIN_ID and uid == ADMIN_ID:
        return True
    try:
        m = await context.bot.get_chat_member(update.effective_chat.id, uid)
        return m.status in ['administrator','creator']
    except:
        return False

# --- ALL COMMAND FUNCTIONS DEFINED HERE ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 DNA Bot is LIVE!\nNew Era Army is secured!\nUse /help")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Commands:\n/start - Alive check\n/help - This list\n/ban - Ban user (admin)\n/unban - Unban\n/mute - Mute\n/unmute - Unmute\n/warn - Warn user\n/blacklist - Add word to blacklist")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        return await update.message.reply_text("❌ Admin only")
    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to user to ban")
    user = update.message.reply_to_message.from_user
    banned_users.add(user.id)
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"🔨 Banned {user.first_name}")
    except Exception as e:
        await update.message.reply_text(f"Banned locally: {e}")

async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return
    user = update.message.reply_to_message.from_user
    banned_users.discard(user.id)
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, user.id)
        await update.message.reply_text(f"✅ Unbanned {user.first_name}")
    except:
        await update.message.reply_text("Unbanned locally")

async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return
    user = update.message.reply_to_message.from_user
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, user.id, ChatPermissions(can_send_messages=False), until_date=timedelta(hours=1))
        await update.message.reply_text(f"🔇 Muted {user.first_name} for 1hr")
    except Exception as e:
        await update.message.reply_text(f"Mute failed: {e}")

async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return
    user = update.message.reply_to_message.from_user
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, user.id, ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
        await update.message.reply_text(f"🔊 Unmuted {user.first_name}")
    except:
        await update.message.reply_text("Unmuted")

async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not update.message.reply_to_message: return
    uid = update.message.reply_to_message.from_user.id
    warnings[uid] = warnings.get(uid, 0) + 1
    if warnings[uid] >= 3:
        await update.message.reply_text(f"⚠️ 3/3 warns - banning")
        try: await context.bot.ban_chat_member(update.effective_chat.id, uid)
        except: pass
    else:
        await update.message.reply_text(f"⚠️ Warned {warnings[uid]}/3")

async def add_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context): return
    if not context.args: return await update.message.reply_text("Usage: /blacklist word")
    word = " ".join(context.args).lower()
    blacklist.add(word)
    await update.message.reply_text(f"✅ Added '{word}' to blacklist")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    uid = update.effective_user.id
    text = update.message.text.lower()

    # Blacklist check
    for b in blacklist:
        if b in text:
            try: await update.message.delete()
            except: pass
            return

    # Spam check
    now = time.time()
    user_messages[uid] = [t for t in user_messages[uid] if now-t < SPAM_TIME]
    user_messages[uid].append(now)
    if len(user_messages[uid]) >= SPAM_LIMIT:
        try: await update.message.delete()
        except: pass
        await update.message.reply_text(f"🐢 Slow down {update.effective_user.first_name}")

def main():
    if not TOKEN:
        print("ERROR: BOT_TOKEN not set in Environment!")
        return
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
    print("Bot is running... polling started!")
    application.run_polling()

if __name__ == '__main__':
    main()
