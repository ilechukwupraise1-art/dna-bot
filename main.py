import os,time,asyncio
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import Update,ChatPermissions
from telegram.ext import Application,CommandHandler,MessageHandler,ContextTypes,filters

TOKEN=os.environ['TOKEN']
user_messages=defaultdict(list)
warnings={}
muted_users={}
banned_users=set()
blacklist=set()
SPAM_LIMIT=5
SPAM_TIME=10

async def check_spam(uid):
 if uid in banned_users or uid in muted_users:return False
 now=time.time()
 user_messages[uid]=[t for t in user_messages[uid] if now-t<SPAM_TIME]
 user_messages[uid].append(now)
 return len(user_messages[uid])>=SPAM_LIMIT

async def is_admin(u,c):
 try:admins=await c.bot.get_chat_administrators(u.effective_chat.id);return u.effective_user.id in [a.user.id for a in admins]
 except:return False

async def get_target(u,c):
 if u.message.reply_to_message:usr=u.message.reply_to_message.from_user;return usr.id,usr.first_name
 return None,None

async def start(u,c):await u.message.reply_text("✅ DNA Bot V3.8 ON\nReply user + /ban /mute /warn /report")
async def help_cmd(u,c):await u.message.reply_text("**DNA BOT V3.8**\n\n**EVERYONE:**\n`/report` Reply+reason\n`/id` Reply user\n`/ping` `/help`\n\n**ADMINS REPLY:**\n`/ban` `/kick` `/mute` `/unmute` `/warn` `/warns` `/clear`\n\n**ADMINS REPLY:**\n`/blacklist` `/unblacklist`\n\n**ADMINS:**\n`/lock links` `/unlock links`\n`/chatid` `/stats` `/spamcheck`",parse_mode="Markdown")
async def ping_cmd(u,c):await u.message.reply_text("🏓 Pong!")
async def id_cmd(u,c):
 tid,name=await get_target(u,c)
 if tid:await u.message.reply_text(f"ID {name}: `{tid}`",parse_mode="Markdown")
 else:await u.message.reply_text(f"Reply user\nYour ID: `{u.effective_user.id}`",parse_mode="Markdown")
async def chatid_cmd(u,c):
 if not await is_admin(u,c):return
 await u.message.reply_text(f"Group ID: `{u.effective_chat.id}`",parse_mode="Markdown")
async def stats_cmd(u,c):
 if not await is_admin(u,c):return
 await u.message.reply_text(f"**STATS**\nBanned:{len(banned_users)}\nMuted:{len(muted_users)}\nBlacklist:{len(blacklist)}\nWarns:{len(warnings)}",parse_mode="Markdown")

async def ban_cmd(u,c):
 if not await is_admin(u,c):return await u.message.reply_text("❌ Not admin")
 tid,name=await get_target(u,c)
 if not tid:return await u.message.reply_text("❌ Reply user")
 try:banned_users.add(tid);await c.bot.ban_chat_member(u.effective_chat.id,tid);await u.message.reply_text(f"✅ {name} banned")
 except Exception as e:await u.message.reply_text(f"❌ {e}")

async def kick_cmd(u,c):
 if not await is_admin(u,c):return
 tid,name=await get_target(u,c)
 if not tid:return await u.message.reply_text("❌ Reply user")
 try:await c.bot.ban_chat_member(u.effective_chat.id,tid);await asyncio.sleep(0.5);await c.bot.unban_chat_member(u.effective_chat.id,tid);await u.message.reply_text(f"👢 {name} kicked")
 except Exception as e:await u.message.reply_text(f"❌ {e}")

async def mute_cmd(u,c):
 if not await is_admin(u,c):return await u.message.reply_text("❌ Not admin")
 tid,name=await get_target(u,c)
 if not tid:return await u.message.reply_text("❌ Reply user")
 until=datetime.now()+timedelta(hours=1)
 muted_users[tid]=until.timestamp()
 try:await c.bot.restrict_chat_member(chat_id=u.effective_chat.id,user_id=tid,permissions=ChatPermissions(can_send_messages=False),until_date=until);await u.message.reply_text(f"🔇 {name} muted 1hr")
 except Exception as e:await u.message.reply_text(f"❌ {e}")

async def unmute_cmd(u,c):
 if not await is_admin(u,c):return
 tid,name=await get_target(u,c)
 if not tid:return await u.message.reply_text("❌ Reply user")
 muted_users.pop(tid,None)
 try:await c.bot.restrict_chat_member(u.effective_chat.id,tid,permissions=ChatPermissions(can_send_messages=True));await u.message.reply_text(f"🔊 {name} unmuted")
 except Exception as e:await u.message.reply_text(f"❌ {e}")

async def warn_cmd(u,c):
 if not await is_admin(u,c):return await u.message.reply_text("❌ Not admin")
 tid,name=await get_target(u,c)
 if not tid:return await u.message.reply_text("❌ Reply user")
 warnings[tid]=warnings.get(tid,0)+1
 if warnings[tid]>=3:await ban_cmd(u,c);return
 await u.message.reply_text(f"⚠️ {name} warned {warnings[tid]}/3")

async def warns_cmd(u,c):
 if not await is_admin(u,c):return
 tid,name=await get_target(u,c)
 if not tid:return await u.message.reply_text("❌ Reply user")
 await u.message.reply_text(f"{name}: {warnings.get(tid,0)} warns")

async def clear_cmd(u,c):
 if not await is_admin(u,c):return
 d=0
 for i in range(10):
  try:await c.bot.delete_message(u.effective_chat.id,u.message_id-i);d+=1
  except:pass
 await u.message.reply_text(f"🗑️ Deleted {d}")

async def blacklist_cmd(u,c):
 if not await is_admin(u,c):return await u.message.reply_text("❌ Not admin")
 tid,name=await get_target(u,c)
 if not tid:return await u.message.reply_text("❌ Reply user")
 blacklist.add(tid)
 try:await c.bot.ban_chat_member(u.effective_chat.id,tid);await u.message.reply_text(f"🚫 {name} blacklisted + banned")
 except:await u.message.reply_text(f"🚫 {name} added to blacklist")

async def unblacklist_cmd(u,c):
 if not await is_admin(u,c):return await u.message.reply_text("❌ Not admin")
 tid,name=await get_target(u,c)
 if not tid:return await u.message.reply_text("❌ Reply user")
 blacklist.discard(tid);await u.message.reply_text(f"✅ {name} removed from blacklist")

async def spamcheck_cmd(u,c):
 if not await is_admin(u,c):return
 await u.message.reply_text(f"Antispam: {SPAM_LIMIT} in {SPAM_TIME}s")

async def lock_cmd(u,c):
 if not await is_admin(u,c):return
 if c.args and c.args[0]=="links":await c.bot.set_chat_permissions(u.effective_chat.id,ChatPermissions(can_add_web_page_previews=False));await u.message.reply_text("🔒 Links locked")

async def unlock_cmd(u,c):
 if not await is_admin(u,c):return
 if c.args and c.args[0]=="links":await c.bot.set_chat_permissions(u.effective_chat.id,ChatPermissions(can_add_web_page_previews=True));await u.message.reply_text("🔓 Links unlocked")

async def report_cmd(u,c):
 if not u.message.reply_to_message:return await u.message.reply_text("❌ Reply bad msg")
 rep=u.message.reply_to_message.from_user;reason=" ".join(c.args) if c.args else "No reason"
 admins=await c.bot.get_chat_administrators(u.effective_chat.id)
 text=f"🚨 **REPORT**\nReported:{rep.first_name} `{rep.id}`\nBy:{u.effective_user.first_name}\nReason:{reason}\nMsg:{u.message.reply_to_message.text[:150]}"
 s=0
 for a in admins:
  if not a.user.is_bot:
   try:await c.bot.send_message(a.user.id,text,parse_mode="Markdown");s+=1
   except:pass
 await u.message.reply_text(f"✅ Sent to {s} admins")

async def handle_message(u,c):
 if not u.message or not u.message.text:return
 uid=u.effective_user.id;txt=u.message.text.lower()
 if uid in muted_users and time.time()>muted_users[uid]:muted_users.pop(uid)
 if uid in banned_users or uid in muted_users or uid in blacklist:
  try:await u.message.delete()
  except:pass;return
 if await check_spam(uid):
  try:await u.message.delete()
  except:pass
  await u.message.reply_text("⚠️ Stop spamming!");await warn_cmd(u,c)

def main():
 app=Application.builder().token(TOKEN).build()
 app.add_handler(CommandHandler("start",start))
 app.add_handler(CommandHandler("help",help_cmd))
 app.add_handler(CommandHandler("ping",ping_cmd))
 app.add_handler(CommandHandler("id",id_cmd))
 app.add_handler(CommandHandler("chatid",chatid_cmd))
 app.add_handler(CommandHandler("stats",stats_cmd))
 app.add_handler(CommandHandler("ban",ban_cmd))
 app.add_handler(CommandHandler("kick",kick_cmd))
 app.add_handler(CommandHandler("mute",mute_cmd))
 app.add_handler(CommandHandler("unmute",unmute_cmd))
 app.add_handler(CommandHandler("warn",warn_cmd))
 app.add_handler(CommandHandler("warns",warns_cmd))
 app.add_handler(CommandHandler("clear",clear_cmd))
 app.add_handler(CommandHandler("blacklist",blacklist_cmd))
 app.add_handler(CommandHandler("unblacklist",unblacklist_cmd))
 app.add_handler(CommandHandler("spamcheck",spamcheck_cmd))
 app.add_handler(CommandHandler("lock",lock_cmd))
 app.add_handler(CommandHandler("unlock",unlock_cmd))
 app.add_handler(CommandHandler("report",report_cmd))
 app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle_message))
 print("DNA Bot V3.8 Running...")
 app.run_polling()

if __name__=="__main__":
 main()
