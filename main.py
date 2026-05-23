import logging
import json
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import google.generativeai as genai

# =============================================
# CONFIG — ক্রেডেনশিয়ালস ও ব্র্যান্ডিং
# =============================================
BOT_TOKEN = "7726729754:AAG7H4R5PLT3ZWoPFgaWchExK9Gk"
GEMINI_KEY = "AIzaSyBzsiIVtoCKd7M0sN8"
ADMIN_IDS = [6423903661, 6511682794]
DEFAULT_SUPPORT = "https://t.me/SAFIN_AHMED_1"

# =============================================
# DATA FILES SYSTEM
# =============================================
USERS_FILE = "users.json"
SETTINGS_FILE = "settings.json"

def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_settings():
    return load_json(SETTINGS_FILE, {
        "force_join": [],
        "free_limit": 5,
        "is_free": False,
        "buttons": [],
        "support_link": DEFAULT_SUPPORT,
        "banned_users": []
    })

def get_users():
    return load_json(USERS_FILE, {})

def save_user(user_id, username, first_name):
    users = get_users()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "username": username or "None",
            "name": first_name or "User",
            "searches": 0,
            "joined": str(__import__('datetime').date.today()),
            "is_premium": False
        }
        save_json(USERS_FILE, users)

def get_user_searches(user_id):
    users = get_users()
    return users.get(str(user_id), {}).get("searches", 0)

def increment_search(user_id):
    users = get_users()
    uid = str(user_id)
    if uid in users:
        users[uid]["searches"] += 1
        save_json(USERS_FILE, users)

# =============================================
# GEMINI AI SETUP — Redox AI configuration
# =============================================
logging.basicConfig(level=logging.INFO)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

SYSTEM_PROMPT = """You are Redox Website Research AI Assistant. When asked about a website provide:
🗓️ Launch Date, 👤 Owner, 🌍 Country, ⭐ Rating/5, 🔒 Safety, 📧 Contact, 📊 Traffic, 💡 Key Facts, ✅ Verdict
Only provide valid info. Respond in Bengali."""

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
        keyboard.append([InlineKeyboardButton(f"📢 Join {name}", url=f"https://t.me/{name}")])
    keyboard.append([InlineKeyboardButton("✅ Check Membership", callback_data="check_join")])
    msg = update.message if hasattr(update, 'message') and update.message else update
    await msg.reply_text(
        "⚠️ *বট ব্যবহার করতে প্রথমে আমাদের চ্যানেলগুলোতে জয়েন করো ভাই!*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================================
# START (MAIN MENU INTERFACE)
# =============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    settings = get_settings()
    
    if user.id in settings.get("banned_users", []):
        await update.message.reply_text("❌ দুঃখিত ভাই, আপনাকে এই বট থেকে ব্লক করা হয়েছে।")
        return

    save_user(user.id, user.username, user.first_name)

    not_joined = await check_force_join(user.id, context)
    if not_joined:
        await force_join_message(update, not_joined)
        return

    users = get_users()
    is_premium = users.get(str(user.id), {}).get("is_premium", False)
    searches = get_user_searches(user.id)
    limit = settings.get("free_limit", 5)
    
    if is_premium or settings.get("is_free", False):
        limit_text = "👑 Premium Mode: Unlimited ♾️"
    else:
        limit_text = f"🔢 আজকের লিমিট: {searches}/{limit}"

    reply_keyboard = [
        [KeyboardButton("📲 Get Website Info"), KeyboardButton("🌍 Available Sites")],
        [KeyboardButton("✅ Active Research"), KeyboardButton("☎️ Support")],
        [KeyboardButton("📂 Research Guide"), KeyboardButton("💳 Premium Access")]
    ]
    
    if user.id in ADMIN_IDS:
        reply_keyboard.append([KeyboardButton("⚙️ Admin Control Panel")])

    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=False)

    await update.message.reply_text(
        f"🌐 *Welcome to Redox Website Research AI*\n\n"
        f"যেকোনো ওয়েবসাইটের ভেতরকার সব সিকিউরিটি ও মালিকানার তথ্য বের করুন এক সেকেন্ডে!\n\n"
        f"🛡️ *ফিচারসমূহ:*\n"
        f"▪️ ডোমেইন খোলার তারিখ ও বয়স\n"
        f"▪️ আসল মালিক ও দেশের নাম\n"
        f"▪️ রিয়েল রিভিউ ও স্ক্যাম রিপোর্ট\n"
        f"▪️ লাইভ ট্রাফিক এনালাইসিস\n\n"
        f"📊 *আপনার স্ট্যাটাস:* {limit_text}\n\n"
        f"👇 নিচের কিবোর্ড থেকে বাটন চাপুন অথবা সরাসরি ডোমেইন নাম টাইপ করুন:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# =============================================
# ALL-IN-ONE ADMIN PANEL INTERFACE
# =============================================
async def get_admin_markup():
    keyboard = [
        [InlineKeyboardButton("📢 Force Join", callback_data="adm_fj"), InlineKeyboardButton("🔢 Search Limit", callback_data="adm_limit")],
        [InlineKeyboardButton("📣 Broadcast Msg", callback_data="adm_bc"), InlineKeyboardButton("🚫 Ban/Unban User", callback_data="adm_ban")],
        [InlineKeyboardButton("👑 Give Premium", callback_data="adm_prem"), InlineKeyboardButton("📂 DB Backup (JSON)", callback_data="adm_backup")],
        [InlineKeyboardButton("📊 Detailed Stats", callback_data="adm_stats")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def get_admin_text():
    settings = get_settings()
    users = get_users()
    total_users = len(users)
    banned_count = len(settings.get("banned_users", []))
    premium_count = sum(1 for u in users.values() if u.get("is_premium", False))
    
    return (
        f"👑 *Redox AI — বিশ্বমানের অ্যাডমিন প্যানেল* 👑\n\n"
        f"👥 মোট ইউজার: {total_users} জন\n"
        f"👑 প্রিমিয়াম মেম্বার: {premium_count} জন\n"
        f"🚫充 ব্লকড ইউজার: {banned_count} জন\n"
        f"📢 ফোর্স জয়েন: {len(settings.get('force_join', []))} টি চ্যানেল\n"
        f"⚙️ সিস্টেম মোড: {'সম্পূর্ণ ফ্রি ♾️' if settings.get('is_free') else 'লিমিট মোড 🔒'}\n\n"
        f"নিচের ইনলাইন মেনু থেকে যেকোনো কনফিগারেশন কন্ট্রোল করুন ভাই:"
    )

async def admin_panel_msg(chat_id, context):
    text = await get_admin_text()
    markup = await get_admin_markup()
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown", reply_markup=markup)

# =============================================
# ADMIN CALLBACK QUERY HANDLER
# =============================================
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if user_id not in ADMIN_IDS:
        await query.answer("❌ আপনি অ্যাডমিন প্যানেল ব্যবহারের যোগ্য নন!", show_alert=True)
        return

    settings = get_settings()
    back_btn = [[InlineKeyboardButton("🔙 প্রধান মেনু", callback_data="adm_main")]]

    if query.data == "adm_main":
        text = await get_admin_text()
        markup = await get_admin_markup()
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=markup)

    elif query.data == "adm_fj":
        channels = settings.get("force_join", [])
        ch_list = "\n".join([f"• {c}" for c in channels]) if channels else "কোনো চ্যানেল সেট করা নেই।"
        await query.edit_message_text(
            f"📢 *ফোর্স জয়েন সেটিংস*\n\nবর্তমান চ্যানেলসমূহ:\n{ch_list}\n\n"
            f"➕ চ্যানেল যুক্ত করতে: `/addfj @ChannelName`\n"
            f"➖ চ্যানেল বাদ দিতে: `/removefj @ChannelName`",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_btn)
        )

    elif query.data == "adm_limit":
        await query.edit_message_text(
            f"🔢 *সার্চ লিমিট কনফিগারেশন*\n\n"
            f"বর্তমান ফ্রি লিমিট: {settings.get('free_limit', 5)} টি/দিন\n\n"
            f"👉 নতুন লিমিট দিতে লেখেন: `/setlimit ১০`\n"
            f"👉 বটের লিমিট তুলে সবাইকে আনলিমিটেড দিতে: `/setfree`\n"
            f"👉 আবার লিমিট সিস্টেম চালু করতে: `/setpaid`",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_btn)
        )

    elif query.data == "adm_bc":
        await query.edit_message_text(
            "📣 *গ্লোবাল ব্রডকাস্ট সিস্টেম*\n\n"
            "বটের সব ইউজারের কাছে একসাথে নোটিফিকেশন বা মেসেজ পাঠাতে ব্যবহার করুন:\n\n"
            "👉 কমান্ড ফরম্যাট: `/broadcast আপনার মেসেজটি এখানে লিখুন`",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_btn)
        )

    elif query.data == "adm_ban":
        await query.edit_message_text(
            "🚫 *ইউজার ব্যান/আনব্যান ম্যানেজমেন্ট*\n\n"
            "কোনো স্প্যামার বা দুষ্ট ইউজারকে বট থেকে চিরতরে ব্লক বা রিলিজ করতে:\n\n"
            "👉 ব্যান করতে: `/ban UserID`\n"
            "👉 আনব্যান করতে: `/unban UserID`",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_btn)
        )

    elif query.data == "adm_prem":
        await query.edit_message_text(
            "👑 *প্রিমিয়াম মেম্বারশিপ কন্ট্রোল*\n\n"
            "কোনো স্পেশাল কাস্টমারকে আনলিমিটেড লাইফটাইম অ্যাক্সেস দিতে ব্যবহার করুন:\n\n"
            "👉 প্রিমিয়াম দিতে: `/addpremium UserID`\n"
            "👉 প্রিমিয়াম বাতিল করতে: `/removepremium UserID`",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_btn)
        )

    elif query.data == "adm_backup":
        if os.path.exists(USERS_FILE):
            await context.bot.send_document(chat_id=user_id, document=open(USERS_FILE, 'rb'), filename="redox_users_database.json", caption="📦 Redox Live Users Database Backup.")
            await query.edit_message_text("✅ ডাটাবেজ ফাইল সরাসরি আপনার ইনবক্সে পাঠানো হয়েছে ভাই!", reply_markup=InlineKeyboardMarkup(back_btn))
        else:
            await query.edit_message_text("❌ ডাটাবেজ ফাইলটি এখনো তৈরি হয়নি।", reply_markup=InlineKeyboardMarkup(back_btn))

    elif query.data == "adm_stats":
        users = get_users()
        total_searches = sum(u.get("searches", 0) for u in users.values())
        await query.edit_message_text(
            f"📊 *গ্লোবাল অ্যাক্টিভিটি রিপোর্ট*\n\n"
            f"🔹 মোট রেজিস্টার্ড ইউজার: {len(users)} জন\n"
            f"🔹 এআই প্রম্পট জেনারেট হয়েছে: {total_searches} বার\n"
            f"🔹 সার্ভার কোড স্ট্যাটাস: সচল ও সুরক্ষিত ✅",
            parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(back_btn)
        )

# =============================================
# ADMIN TEXT COMMAND EXECUTORS
# =============================================
async def admin_commands_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    text = update.message.text
    cmd = text.split()[0].lower()
    settings = get_settings()
    users = get_users()

    if cmd == "/addfj" and context.args:
        ch = context.args[0]
        if ch not in settings["force_join"]:
            settings["force_join"].append(ch)
            save_json(SETTINGS_FILE, settings)
            await update.message.reply_text(f"✅ চ্যানেল `{ch}` ফোর্স জয়েন তালিকায় যোগ হয়েছে।")

    elif cmd == "/removefj" and context.args:
        ch = context.args[0]
        if ch in settings["force_join"]:
            settings["force_join"].remove(ch)
            save_json(SETTINGS_FILE, settings)
            await update.message.reply_text(f"✅ চ্যানেল `{ch}` ফোর্স জয়েন তালিকা থেকে বাদ দেওয়া হয়েছে।")

    elif cmd == "/setlimit" and context.args:
        try:
            limit = int(context.args[0])
            settings["free_limit"] = limit
            settings["is_free"] = False
            save_json(SETTINGS_FILE, settings)
            await update.message.reply_text(f"✅ দৈনিক ফ্রি সার্চ লিমিট `{limit}` টি সেট করা হয়েছে।")
        except:
            await update.message.reply_text("❌ সঠিক সংখ্যা লিখুন। উদাহরণ: `/setlimit 10`")

    elif cmd == "/setfree":
        settings["is_free"] = True
        save_json(SETTINGS_FILE, settings)
        await update.message.reply_text("✅ সিস্টেম মোড পরিবর্তন সফল! বট এখন সবার জন্য আনলিমিটেড ফ্রি।")

    elif cmd == "/setpaid":
        settings["is_free"] = False
        save_json(SETTINGS_FILE, settings)
        await update.message.reply_text("✅ লিমিট সিস্টেম পুনরায় সক্রিয় করা হয়েছে।")

    elif cmd == "/ban" and context.args:
        target = context.args[0]
        if int(target) not in settings["banned_users"]:
            settings["banned_users"].append(int(target))
            save_json(SETTINGS_FILE, settings)
            await update.message.reply_text(f"🚫 ইউজার `{target}` কে বট থেকে ব্লক করা হয়েছে।")

    elif cmd == "/unban" and context.args:
        target = int(context.args[0])
        if target in settings["banned_users"]:
            settings["banned_users"].remove(target)
            save_json(SETTINGS_FILE, settings)
            await update.message.reply_text(f"✅ ইউজার `{target}` কে আনব্যান করা হয়েছে।")

    elif cmd == "/addpremium" and context.args:
        target = context.args[0]
        if target in users:
            users[target]["is_premium"] = True
            save_json(USERS_FILE, users)
            await update.message.reply_text(f"👑 ইউজার `{target}` কে সফলভাবে প্রিমিয়াম মেম্বারশিপ দেওয়া হয়েছে।")
        else:
            await update.message.reply_text("❌ এই আইডি ওয়ালা কোনো ইউজার ডাটাবেজে নেই।")

    elif cmd == "/removepremium" and context.args:
        target = context.args[0]
        if target in users:
            users[target]["is_premium"] = False
            save_json(USERS_FILE, users)
            await update.message.reply_text(f"✅ ইউজার `{target}` এর প্রিমিয়াম লাইসেন্স বাতিল করা হয়েছে।")

    elif cmd == "/broadcast" and context.args:
        msg_body = text.split(None, 1)[1]
        success = failed = 0
        await update.message.reply_text(f"📣 {len(users)} জন ইউজারের কাছে গ্লোবাল মেসেজ পাঠানো শুরু হচ্ছে...")
        for uid in users:
            try:
                await context.bot.send_message(chat_id=int(uid), text=f"📢 *Redox AI অফিসিয়াল নোটিশ*\n\n{msg_body}", parse_mode="Markdown")
                success += 1
            except:
                failed += 1
        await update.message.reply_text(f"🏁 ব্রডকাস্ট সম্পন্ন!\n✅ সফল: {success}\n❌ ব্যর্থ: {failed}")

# =============================================
# LIVE USER INTERACTION & GEMINI EXECUTION
# =============================================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    settings = get_settings()

    if user.id in settings.get("banned_users", []):
        return

    save_user(user.id, user.username, user.first_name)
    text = update.message.text.strip()

    # অ্যাডমিন প্যানেল কন্ট্রোল
    if text == "⚙️ Admin Control Panel" and user.id in ADMIN_IDS:
        await admin_panel_msg(update.message.chat_id, context)
        return

    # রিপ্লাই কিবোর্ড বাটনের রেসপন্স
    if text == "📲 Get Website Info":
        await update.message.reply_text("🔍 যেকোনো ওয়েবসাইটের ডোমেইন নাম চ্যাটে লিখে পাঠান।\n\n👉 উদাহরণ: `quotex.com` বা `google.com`")
        return
    elif text == "🌍 Available Sites":
        await update.message.reply_text("🌍 *সাপোর্টেড নেটওয়ার্কস*\n\nবিশ্বের সব ধরনের লাইভ এবং পাবলিক ডোমেন এই বট সাপোর্ট করে ভাই।")
        return
    elif text == "✅ Active Research":
        await update.message.reply_text("🔬 Redox AI রিসার্চ ইঞ্জিন অ্যাক্টিভ ও অনলাইন আছে। আপনার কাঙ্ক্ষিত লিঙ্কটি টাইপ করুন।")
        return
    elif text == "☎️ Support":
        await update.message.reply_text(f"☎️ যেকোনো সমস্যা বা প্রিমিয়াম এক্সেসের জন্য আমাদের অফিশিয়াল ওনার সাপোর্টে যোগাযোগ করুন ভাই:\n\n💬 @SAFIN_AHMED_1")
        return
    elif text == "📂 Research Guide":
        await update.message.reply_text("📖 *ইউজার গাইড*\n\n১. নিচে সরাসরি সাইটের লিঙ্ক দিন।\n২. আমাদের আপগ্রেডেড Redox AI ইঞ্জিন সাইটটির ব্যাকএন্ড হিস্টোরি এনালাইসিস করে সম্পূর্ণ সত্য রিপোর্ট পেশ করবে।")
        return
    elif text == "💳 Premium Access":
        await update.message.reply_text(f"💳 *Redox AI প্রিমিয়াম মেম্বারশিপ*\n\n实时 লিমিট ছাড়া চোখের পলকে সুপারফাস্ট রেজাল্ট এবং আনলিমিটেড এআই জেনারেশন ফিচার এনজয় করতে প্রিমিয়াম অ্যাক্টিভেট করে নিন।\n\nContact Admin: @SAFIN_AHMED_1")
        return

    if text.startswith("/"):
        await admin_commands_handler(update, context)
        return

    # ফোর্স জয়েন চেক
    not_joined = await check_force_join(user.id, context)
    if not_joined:
        await force_join_message(update, not_joined)
        return

    # মেম্বার টাইপ ও লিমিট ভেরিফিকেশন
    users = get_users()
    is_premium = users.get(str(user.id), {}).get("is_premium", False)
    if not is_premium and not settings.get("is_free", False):
        searches = get_user_searches(user.id)
        limit = settings.get("free_limit", 5)
        if searches >= limit:
            await update.message.reply_text(f"❌ *আপনার আজকের ফ্রি লিমিট শেষ!* \n\nলিমিট রিমুভ করতে বা প্রিমিয়াম অ্যাক্সেস পেতে ডেডিকেটেড অ্যাডমিন প্যানেলে যোগাযোগ করুন ভাই।\n\nContact Admin: @SAFIN_AHMED_1")
            return

    status_msg = await update.message.reply_text(f"🔍 *{text}* ডোমেইনটি গভীরভাবে এনালাইসিস করা হচ্ছে...\n\n⏳ অনুগ্রহ করে কয়েক সেকেন্ড অপেক্ষা করুন ভাই...", parse_mode="Markdown")

    try:
        prompt = f"{SYSTEM_PROMPT}\n\nএই website সম্পর্কে সব তথ্য দাও: {text}"
        response = model.generate_content(prompt)
        result = response.text
        increment_search(user.id)
    except Exception as e:
        result = f"❌ *Redox Engine Error:* {str(e)}"

    keyboard = [[InlineKeyboardButton("🔄 New Search", callback_data="research")]]
    await status_msg.reply_text(result, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# =============================================
# INLINE ACTION CALLBACKS
# =============================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("adm_"):
        await admin_callback(update, context)
        return

    if query.data == "research":
        await query.message.reply_text("🔍 যেকোনো ওটিপি পোর্টাল বা ট্রেডিং ওয়েবসাইটের নাম ইনবক্সে টাইপ করুন:")
    elif query.data == "check_join":
        not_joined = await check_force_join(query.from_user.id, context)
        if not_joined:
            await query.answer("❌ আপনি এখনো সব চ্যানেলে জয়েন করেননি ভাই!", show_alert=True)
        else:
            await query.edit_message_text("✅ মেম্বারশিপ ভেরিফাইড! বট অ্যাক্টিভেট করতে পুনরায় একবার /start কমান্ডটি দিন।")

# =============================================
# APPLICATION ENGINE EXECUTION
# =============================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.COMMAND, admin_commands_handler))

    print("🚀 Redox Website Research AI Engine Successfully Started!")
    app.run_polling()

if __name__ == "__main__":
    main()
