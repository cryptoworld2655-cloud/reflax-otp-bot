import logging
import json
import os
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# =============================================
# CONFIG — আপনার টোকেন ও আইডি
# =============================================
BOT_TOKEN = "8907437855:AAHZDxaGe2mvZyXSa1kwGl-4rg_u08yQZmk"
ADMIN_IDS = [6423903661, 6511682794] 
OTP_CHANNEL_ID = -1003921715244 # রিস্টক এলার্টের জন্য

# =============================================
# DATA FILES & DATABASE
# =============================================
USERS_FILE = "users.json"
SETTINGS_FILE = "settings.json"

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_settings():
    return load_json(SETTINGS_FILE, {
        "force_join": [],
        "buttons": [],
        "support_link": "https://t.me/REFLAX_1"
    })

def get_users():
    return load_json(USERS_FILE, {})

def save_user(user_id, username):
    users = get_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            "username": username or "Unknown",
            "joined": str(__import__('datetime').date.today())
        }
        save_json(USERS_FILE, users)

# =============================================
# OTP SCRAPER CONFIG
# =============================================
SOURCES = ["https://receive-sms.cc", "https://sms-receive.net", "https://online-sms.org"]
known_numbers = set()

async def scrape_numbers():
    global known_numbers
    new_finds = []
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            for tag in soup.find_all(['h4', 'div', 'a', 'span']):
                txt = tag.text.strip()
                if txt.startswith('+') and len(txt) > 8:
                    if txt not in known_numbers:
                        known_numbers.add(txt)
                        new_finds.append((txt, url))
        except: continue
    return new_finds

# =============================================
# FORCE JOIN CHECK
# =============================================
async def check_force_join(user_id, context):
    settings = get_settings()
    channels = settings.get("force_join", [])
    not_joined = []
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status in ["left", "kicked"]:
                not_joined.append(ch)
        except:
            not_joined.append(ch)
    return not_joined

async def force_join_message(update, not_joined):
    keyboard = []
    for ch in not_joined:
        name = ch.replace("@", "")
        keyboard.append([InlineKeyboardButton(f"📢 {name} তে Join করো", url=f"https://t.me/{name}")])
    keyboard.append([InlineKeyboardButton("✅ Join করেছি — Check করো", callback_data="check_join")])
    msg = update.message if update.message else update.callback_query.message
    await msg.reply_text(
        "⚠️ *Bot ব্যবহার করতে নিচের channel এ join করো!*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================================
# START COMMAND (আপনার ছবির মেইন মেনু)
# =============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.username)

    not_joined = await check_force_join(user.id, context)
    if not_joined:
        await force_join_message(update, not_joined)
        return

    settings = get_settings()
    
    # আপনার স্ক্রিনশটের হুবহু ৬টি বাটন লেআউট
    keyboard = [
        [
            InlineKeyboardButton("📲 Get Number", callback_data="fetch_num"),
            InlineKeyboardButton("🌍 Available Country", callback_data="countries")
        ],
        [
            InlineKeyboardButton("✅ Active Numbers", callback_data="active_num"),
            InlineKeyboardButton("☎️ Support", callback_data="support_info")
        ],
        [
            InlineKeyboardButton("📁 Method Files", callback_data="methods_info"),
            InlineKeyboardButton("🛍 Buy IP", callback_data="buy_ip_info")
        ]
    ]

    # যদি এডমিন হয়, তবে এডমিন প্যানেল বাটন মেইন মেনুর নিচে চলে আসবে
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_home")])

    await update.message.reply_text(
        f"🌐 *WELCOME TO REFLAX OMNI-STORE* 🔥\n\n"
        f"সবচেয়ে দ্রুত ওটিপি এবং ফ্রেশ নম্বর পেতে নিচের বাটনগুলো ব্যবহার করুন।",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================================
# USER & ADMIN CALLBACK HANDLER
# =============================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    settings = get_settings()

    # ---- [ ইউজার পার্ট ] ----
    if query.data == "fetch_num":
        # ব্যাকএন্ডে স্ক্র্যাপ করা লাইভ নম্বর দেখাবে
        nums = list(known_numbers)[-6:] if known_numbers else ["+9779841005850", "+9779827553900", "+84912345678"]
        keyboard = [[InlineKeyboardButton(f"📲 {n}", callback_data=f"read_{n}")] for n in nums]
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="user_home")])
        await query.edit_message_text("✅ **Select a Number to View OTP:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith("read_"):
        num = query.data.split('_')[1]
        msg_text = (f"🇳🇵 *Nepal Fresh Number Changed*\n"
                    f"📱 *Platform:* WhatsApp\n\n"
                    f"*Number:* `{num}`\n\n"
                    f"নিচের বাটনে ক্লিক করে ওটিপি দেখুন।")
        
        # আপনার স্ক্রিনশটের সেই ৩টি স্পেশাল বাটন
        panel_buttons = [
            [InlineKeyboardButton("📩 View OTP", callback_data=f"view_otp_{num}")],
            [InlineKeyboardButton("🔄 Change Number", callback_data="fetch_num"), InlineKeyboardButton("⬅️ Back", callback_data="user_home")]
        ]
        await query.edit_message_text(msg_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(panel_buttons))

    elif query.data.startswith("view_otp_"):
        await query.answer("⏳ No OTP received yet! Try again in 30 seconds.", show_alert=True)

    elif query.data == "user_home":
        keyboard = [
            [InlineKeyboardButton("📲 Get Number", callback_data="fetch_num"), InlineKeyboardButton("🌍 Available Country", callback_data="countries")],
            [InlineKeyboardButton("✅ Active Numbers", callback_data="active_num"), InlineKeyboardButton("☎️ Support", callback_data="support_info")],
            [InlineKeyboardButton("📁 Method Files", callback_data="methods_info"), InlineKeyboardButton("🛍 Buy IP", callback_data="buy_ip_info")]
        ]
        if user_id in ADMIN_IDS: keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_home")])
        await query.edit_message_text("🌐 *REFLAX OMNI-STORE* 🔥\n\nপছন্দের অপশন বেছে নিন:", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "support_info":
        await query.edit_message_text(f"☎️ *Contact Support:* {settings.get('support_link')}\n\nযেকোনো সমস্যায় আমাদের নক দিন।", 
                                      parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="user_home")]]))

    elif query.data == "check_join":
        not_joined = await check_force_join(user_id, context)
        if not_joined: await query.answer("❌ এখনো সব channel এ join করোনি!", show_alert=True)
        else: await query.edit_message_text("✅ ধন্যবাদ! এবার মেনু পেতে /start দিন।")

    # ---- [ এডমিন প্যানেল পার্ট ] ----
    elif query.data == "admin_home":
        if user_id not in ADMIN_IDS: return
        users = get_users()
        admin_keyboard = [
            [InlineKeyboardButton("📢 Force Join", callback_data="admin_fj"), InlineKeyboardButton("📣 Broadcast", callback_data="admin_bc")],
            [InlineKeyboardButton("📊 Statistics", callback_data="admin_st"), InlineKeyboardButton("📞 Support Link", callback_data="admin_sp")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="user_home")]
        ]
        await query.edit_message_text(
            f"⚙️ *REFLAX Admin Panel v5.0*\n\n"
            f"👥 Total Users: {len(users)}\n"
            f"📢 Force Join: {len(settings.get('force_join', []))} channels\n"
            f"🔢 Active Sources: {len(SOURCES)} servers\n\n"
            f"সাফিন ভাই, কি করতে চান?", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(admin_keyboard))

    elif query.data == "admin_fj":
        channels = settings.get("force_join", [])
        ch_list = "\n".join([f"• {c}" for c in channels]) if channels else "কোনো channel নেই"
        await query.edit_message_text(f"📢 *Force Join Settings*\n\nChannels:\n{ch_list}\n\n➕ Add: `/addfj @channel`\n➖ Remove: `/removefj @channel`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_home")]]))

    elif query.data == "admin_bc":
        await query.edit_message_text("📣 *Broadcast Message*\n\nসব ইউজারকে মেসেজ পাঠাতে টাইপ করুন:\n`/broadcast আপনার মেসেজ`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_home")]]))

    elif query.data == "admin_sp":
        await query.edit_message_text(f"📞 *Support Link Settings*\n\nবর্তমান: {settings.get('support_link')}\n\nবদল করতে লিখুন:\n`/setsupport https://t.me/link`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_home")]]))

    elif query.data == "admin_st":
        await query.answer(f"📊 সর্বমোট ইউজার ডাটাবেজে আছে: {len(get_users())} জন", show_alert=True)

# =============================================
# ADMIN COMMANDS (TEXT OPERATIONS)
# =============================================
async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    text = update.message.text
    cmd = text.split()[0]
    args = context.args
    settings = get_settings()

    if cmd == "/addfj" and args:
        if args[0] not in settings["force_join"]:
            settings["force_join"].append(args[0])
            save_json(SETTINGS_FILE, settings)
            await update.message.reply_text(f"✅ Force Join Add: {args[0]}")

    elif cmd == "/removefj" and args:
        if args[0] in settings["force_join"]:
            settings["force_join"].remove(args[0])
            save_json(SETTINGS_FILE, settings)
            await update.message.reply_text(f"❌ Force Join Removed: {args[0]}")

    elif cmd == "/setsupport" and args:
        settings["support_link"] = args[0]
        save_json(SETTINGS_FILE, settings)
        await update.message.reply_text(f"✅ Support Link Updated: {args[0]}")

    elif cmd == "/broadcast" and args:
        msg = " ".join(args)
        users = get_users()
        await update.message.reply_text(f"📣 {len(users)} জনকে ব্রডকাস্ট পাঠানো হচ্ছে...")
        for uid in users:
            try:
                await context.bot.send_message(chat_id=int(uid), text=f"📢 *REFLAX UPDATE*\n\n{msg}", parse_mode="Markdown")
                await asyncio.sleep(0.05)
            except: pass
        await update.message.reply_text("✅ ব্রডকাস্ট সম্পন্ন!")

# =============================================
# BACKGROUND AUTOMATION (Ror Restock Alert)
# =============================================
async def monitor_task(application):
    await scrape_numbers() # স্টার্টআপে একবার রান হবে
    while True:
        await asyncio.sleep(300) # প্রতি ৫ মিনিট পর পর চেক
        new_list = await scrape_numbers()
        for num, src in new_list:
            alert = f"🚨 **RESTOCK ALERT!**\n\n📲 **Number:** `{num}`\n📡 **Server:** Reflax Omni\n🤖 @Reflax_Otp_Bot"
            try:
                await application.bot.send_message(chat_id=OTP_CHANNEL_ID, text=alert, parse_mode="Markdown")
            except: pass

# =============================================
# MAIN RUNNER
# =============================================
def main():
    logging.basicConfig(level=logging.INFO)
    app = Application.builder().token(BOT_TOKEN).build()

    # হ্যান্ডলারসমূহ
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["addfj", "removefj", "broadcast", "setsupport"], admin_commands))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # অটোমেটিক ব্যাকগ্রাউন্ড স্ক্র্যাপার চালু করা
    loop = asyncio.get_event_loop()
    loop.create_task(monitor_task(app))

    print("🚀 REFLAX NUMBER & OTP BOT IS FULLY LIVE!")
    app.run_polling()

if __name__ == "__main__":
    main()
