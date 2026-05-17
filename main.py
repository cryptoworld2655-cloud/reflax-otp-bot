import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import google.generativeai as genai

# =============================================
# CONFIG — এখানে তোমার token বসাও
# =============================================
BOT_TOKEN = "8020465907:AAFKnQqMbJVACI0UXiNVocZMGejfdJGJdGM"         # @BotFather থেকে নাও
GEMINI_KEY = "AIzaSyDn0nFjn_kypMJf_cfuU5-BSlFYBt40DHw"       # ai.google.dev থেকে নাও
ADMIN_IDS = [6423903661, 6511682794]                    # তোমার Telegram ID দাও

# =============================================
# DATA FILES
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
        "support_link": "https://t.me/your_support"
    })

def get_users():
    return load_json(USERS_FILE, {})

def save_user(user_id, username):
    users = get_users()
    if str(user_id) not in users:
        users[str(user_id)] = {
            "username": username,
            "searches": 0,
            "joined": str(__import__('datetime').date.today())
        }
        save_json(USERS_FILE, users)

def get_user_searches(user_id):
    users = get_users()
    return users.get(str(user_id), {}).get("searches", 0)

def increment_search(user_id):
    users = get_users()
    if str(user_id) in users:
        users[str(user_id)]["searches"] += 1
        save_json(USERS_FILE, users)

# =============================================
logging.basicConfig(level=logging.INFO)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-pro')

SYSTEM_PROMPT = """You are REFLAX Website Research Assistant. When asked about a website provide:
🗓️ Launch Date, 👤 Owner, 🌍 Country, ⭐ Rating/5, 🔒 Safety, 📧 Contact, 📊 Traffic, 💡 Key Facts, ✅ Verdict
Only public info. Respond in Bengali."""

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
    msg = update.message if hasattr(update, 'message') and update.message else update
    await msg.reply_text(
        "⚠️ *Bot ব্যবহার করতে নিচের channel এ join করো!*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================================
# START
# =============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.username)

    not_joined = await check_force_join(user.id, context)
    if not_joined:
        await force_join_message(update, not_joined)
        return

    settings = get_settings()
    searches = get_user_searches(user.id)
    limit = settings.get("free_limit", 5)
    is_free = settings.get("is_free", False)
    limit_text = "♾️ Unlimited" if is_free else f"🔢 আজকের search: {searches}/{limit}"

    keyboard = [
        [
            InlineKeyboardButton("🔍 Website Research", callback_data="research"),
            InlineKeyboardButton("📋 Help", callback_data="help")
        ],
        [
            InlineKeyboardButton("🔵 Facebook", callback_data="site_facebook.com"),
            InlineKeyboardButton("🔍 Google", callback_data="site_google.com")
        ],
        [
            InlineKeyboardButton("▶️ YouTube", callback_data="site_youtube.com"),
            InlineKeyboardButton("📸 Instagram", callback_data="site_instagram.com")
        ],
        [
            InlineKeyboardButton("✈️ Telegram", callback_data="site_telegram.org"),
            InlineKeyboardButton("🐦 Twitter/X", callback_data="site_x.com")
        ]
    ]

    # Custom buttons যোগ করো
    custom_btns = settings.get("buttons", [])
    row = []
    for btn in custom_btns:
        row.append(InlineKeyboardButton(btn["text"], url=btn["url"]))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton("📞 Support", url=settings.get("support_link", "https://t.me/support"))])

    await update.message.reply_text(
        f"🌐 *REFLAX Website Research AI*\n\n"
        f"যেকোনো website সম্পর্কে জানো!\n\n"
        f"🗓️ Launch date\n"
        f"👤 মালিক কে\n"
        f"⭐ Rating ও Review\n"
        f"🔒 Safe কিনা\n"
        f"📊 Traffic\n\n"
        f"{limit_text}\n\n"
        f"Website এর নাম লেখো 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================================
# ADMIN PANEL
# =============================================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ তুমি admin না!")
        return

    settings = get_settings()
    users = get_users()

    keyboard = [
        [
            InlineKeyboardButton("📢 Force Join", callback_data="admin_forcejoin"),
            InlineKeyboardButton("🔘 Button Add/Remove", callback_data="admin_button")
        ],
        [
            InlineKeyboardButton("📣 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("⚙️ Limit Settings", callback_data="admin_limit")
        ],
        [
            InlineKeyboardButton("📞 Support Link", callback_data="admin_support"),
            InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")
        ]
    ]

    await update.message.reply_text(
        f"⚙️ *REFLAX Admin Panel*\n\n"
        f"👥 Total Users: {len(users)}\n"
        f"📢 Force Join Channels: {len(settings.get('force_join', []))}\n"
        f"🔘 Custom Buttons: {len(settings.get('buttons', []))}\n"
        f"🔢 Limit: {'Unlimited ♾️' if settings.get('is_free') else str(settings.get('free_limit', 5)) + '/day'}\n\n"
        f"কী করতে চাও?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =============================================
# ADMIN CALLBACKS
# =============================================
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in ADMIN_IDS:
        await query.answer("❌ Admin only!", show_alert=True)
        return

    settings = get_settings()
    back_btn = [[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]

    if query.data == "admin_forcejoin":
        channels = settings.get("force_join", [])
        ch_list = "\n".join([f"• {c}" for c in channels]) if channels else "কোনো channel নেই"
        await query.edit_message_text(
            f"📢 *Force Join Settings*\n\n"
            f"বর্তমান channels:\n{ch_list}\n\n"
            f"➕ Channel add: `/addfj @channel`\n"
            f"➖ Channel remove: `/removefj @channel`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_btn)
        )

    elif query.data == "admin_button":
        buttons = settings.get("buttons", [])
        btn_list = "\n".join([f"• {b['text']} → {b['url']}" for b in buttons]) if buttons else "কোনো button নেই"
        await query.edit_message_text(
            f"🔘 *Custom Button Settings*\n\n"
            f"বর্তমান buttons:\n{btn_list}\n\n"
            f"➕ Add: `/addbutton টেক্সট | https://link.com`\n"
            f"➖ Remove: `/removebutton টেক্সট`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_btn)
        )

    elif query.data == "admin_broadcast":
        await query.edit_message_text(
            "📣 *Broadcast Message*\n\n"
            "সব user কে message পাঠাতে:\n\n"
            "`/broadcast তোমার message এখানে লেখো`\n\n"
            "⚠️ এই message সব user পাবে!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_btn)
        )

    elif query.data == "admin_limit":
        await query.edit_message_text(
            f"⚙️ *Limit Settings*\n\n"
            f"বর্তমান: {'Unlimited ♾️' if settings.get('is_free') else str(settings.get('free_limit', 5)) + ' searches/day'}\n\n"
            f"🔢 Limit দাও: `/setlimit 10`\n"
            f"♾️ Free করো: `/setfree`\n"
            f"🔒 Limit ফিরাও: `/setpaid`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_btn)
        )

    elif query.data == "admin_support":
        await query.edit_message_text(
            f"📞 *Support Link*\n\n"
            f"বর্তমান: {settings.get('support_link', 'নেই')}\n\n"
            f"Change: `/setsupport https://t.me/support`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_btn)
        )

    elif query.data == "admin_stats":
        users = get_users()
        await query.edit_message_text(
            f"📊 *Statistics*\n\n"
            f"👥 Total Users: {len(users)}\n"
            f"📢 Force Join: {len(settings.get('force_join', []))} channels\n"
            f"🔘 Buttons: {len(settings.get('buttons', []))}\n"
            f"🔢 Limit: {'Free ♾️' if settings.get('is_free') else str(settings.get('free_limit', 5)) + '/day'}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(back_btn)
        )

    elif query.data == "admin_back":
        users = get_users()
        keyboard = [
            [
                InlineKeyboardButton("📢 Force Join", callback_data="admin_forcejoin"),
                InlineKeyboardButton("🔘 Button Add/Remove", callback_data="admin_button")
            ],
            [
                InlineKeyboardButton("📣 Broadcast", callback_data="admin_broadcast"),
                InlineKeyboardButton("⚙️ Limit Settings", callback_data="admin_limit")
            ],
            [
                InlineKeyboardButton("📞 Support Link", callback_data="admin_support"),
                InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")
            ]
        ]
        await query.edit_message_text(
            f"⚙️ *REFLAX Admin Panel*\n\n👥 Total Users: {len(users)}\n\nকী করতে চাও?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# =============================================
# ADMIN COMMANDS
# =============================================
async def addfj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args:
        await update.message.reply_text("❌ `/addfj @channel`", parse_mode="Markdown"); return
    channel = context.args[0]
    settings = get_settings()
    if channel not in settings["force_join"]:
        settings["force_join"].append(channel)
        save_json(SETTINGS_FILE, settings)
        await update.message.reply_text(f"✅ `{channel}` add হয়েছে!", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ আগেই আছে!")

async def removefj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args:
        await update.message.reply_text("❌ `/removefj @channel`", parse_mode="Markdown"); return
    channel = context.args[0]
    settings = get_settings()
    if channel in settings["force_join"]:
        settings["force_join"].remove(channel)
        save_json(SETTINGS_FILE, settings)
        await update.message.reply_text(f"✅ `{channel}` remove হয়েছে!", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ এই channel নেই!")

async def addbutton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    text = " ".join(context.args)
    if "|" not in text:
        await update.message.reply_text("❌ `/addbutton টেক্সট | https://link.com`", parse_mode="Markdown"); return
    parts = text.split("|", 1)
    settings = get_settings()
    settings["buttons"].append({"text": parts[0].strip(), "url": parts[1].strip()})
    save_json(SETTINGS_FILE, settings)
    await update.message.reply_text(f"✅ Button add হয়েছে!\n`{parts[0].strip()}`", parse_mode="Markdown")

async def removebutton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    btn_text = " ".join(context.args)
    settings = get_settings()
    settings["buttons"] = [b for b in settings["buttons"] if b["text"] != btn_text]
    save_json(SETTINGS_FILE, settings)
    await update.message.reply_text(f"✅ `{btn_text}` remove হয়েছে!", parse_mode="Markdown")

async def setlimit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    try:
        limit = int(context.args[0])
        settings = get_settings()
        settings["free_limit"] = limit
        settings["is_free"] = False
        save_json(SETTINGS_FILE, settings)
        await update.message.reply_text(f"✅ Limit: {limit} searches/day")
    except:
        await update.message.reply_text("❌ `/setlimit 10`", parse_mode="Markdown")

async def setfree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    settings = get_settings()
    settings["is_free"] = True
    save_json(SETTINGS_FILE, settings)
    await update.message.reply_text("✅ Bot সম্পূর্ণ Free! সবাই unlimited use করতে পারবে ♾️")

async def setpaid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    settings = get_settings()
    settings["is_free"] = False
    save_json(SETTINGS_FILE, settings)
    await update.message.reply_text(f"✅ Limit আবার চালু! {settings.get('free_limit', 5)}/day")

async def setsupport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args:
        await update.message.reply_text("❌ `/setsupport https://t.me/support`", parse_mode="Markdown"); return
    settings = get_settings()
    settings["support_link"] = context.args[0]
    save_json(SETTINGS_FILE, settings)
    await update.message.reply_text(f"✅ Support link: {context.args[0]}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    if not context.args:
        await update.message.reply_text("❌ `/broadcast message`", parse_mode="Markdown"); return
    msg = " ".join(context.args)
    users = get_users()
    success = failed = 0
    await update.message.reply_text(f"📣 Broadcast শুরু... ({len(users)} জনকে)")
    for uid in users:
        try:
            await context.bot.send_message(
                chat_id=int(uid),
                text=f"📢 *REFLAX — Admin Message*\n\n{msg}",
                parse_mode="Markdown"
            )
            success += 1
        except:
            failed += 1
    await update.message.reply_text(f"✅ Done!\n✅ Success: {success}\n❌ Failed: {failed}")

# =============================================
# MESSAGE HANDLER
# =============================================
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.username)

    not_joined = await check_force_join(user.id, context)
    if not_joined:
        await force_join_message(update, not_joined)
        return

    settings = get_settings()
    if not settings.get("is_free", False):
        searches = get_user_searches(user.id)
        limit = settings.get("free_limit", 5)
        if searches >= limit:
            await update.message.reply_text(
                f"❌ *আজকের limit শেষ!*\n\n{limit}টি search হয়ে গেছে।\nকাল আবার আসো 🕐\n\nSupport: {settings.get('support_link', '')}",
                parse_mode="Markdown"
            )
            return

    text = update.message.text.strip()
    await update.message.reply_text(f"🔍 *{text}* খুঁজছি...\n\n⏳ অপেক্ষা করো...", parse_mode="Markdown")

    try:
        prompt = f"{SYSTEM_PROMPT}\n\nএই website সম্পর্কে সব তথ্য দাও: {text}"
        response = model.generate_content(prompt)
        result = response.text
        increment_search(user.id)
    except Exception as e:
        result = f"❌ Error: {str(e)}"

    keyboard = [
        [
            InlineKeyboardButton("🔄 আবার Search", callback_data="research"),
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ],
        [InlineKeyboardButton("📞 Support", url=settings.get("support_link", "https://t.me/support"))]
    ]
    await update.message.reply_text(result, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# =============================================
# BUTTON HANDLER
# =============================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("admin_"):
        await admin_callback(update, context)
        return

    settings = get_settings()

    if query.data == "home":
        keyboard = [
            [InlineKeyboardButton("🔍 Research", callback_data="research"), InlineKeyboardButton("📋 Help", callback_data="help")],
            [InlineKeyboardButton("📞 Support", url=settings.get("support_link", "https://t.me/support"))]
        ]
        await query.edit_message_text("🌐 *REFLAX*\n\nWebsite এর নাম লেখো 👇", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "research":
        await query.edit_message_text(
            "🔍 যেকোনো website এর নাম লেখো!\nযেমন: `google.com`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]])
        )

    elif query.data == "help":
        await query.edit_message_text(
            "📖 *Help*\n\n1️⃣ Website এর নাম লেখো\n2️⃣ AI সব তথ্য দেবে\n\nযেমন: `facebook.com`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]])
        )

    elif query.data == "check_join":
        not_joined = await check_force_join(query.from_user.id, context)
        if not_joined:
            await query.answer("❌ এখনো সব channel এ join করোনি!", show_alert=True)
        else:
            await query.edit_message_text("✅ ধন্যবাদ! /start দাও।")

    elif query.data.startswith("site_"):
        site = query.data.replace("site_", "")
        await query.edit_message_text(f"🔍 *{site}* খুঁজছি...\n\n⏳ অপেক্ষা করো...", parse_mode="Markdown")
        try:
            prompt = f"{SYSTEM_PROMPT}\n\nএই website সম্পর্কে তথ্য দাও: {site}"
            response = model.generate_content(prompt)
            result = response.text
        except Exception as e:
            result = f"❌ Error: {str(e)}"

        keyboard = [
            [InlineKeyboardButton("🔄 আবার Search", callback_data="research"), InlineKeyboardButton("🏠 Home", callback_data="home")],
            [InlineKeyboardButton("📞 Support", url=settings.get("support_link", "https://t.me/support"))]
        ]
        await query.edit_message_text(result, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

# =============================================
# MAIN
# =============================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("addfj", addfj))
    app.add_handler(CommandHandler("removefj", removefj))
    app.add_handler(CommandHandler("addbutton", addbutton))
    app.add_handler(CommandHandler("removebutton", removebutton))
    app.add_handler(CommandHandler("setlimit", setlimit))
    app.add_handler(CommandHandler("setfree", setfree))
    app.add_handler(CommandHandler("setpaid", setpaid))
    app.add_handler(CommandHandler("setsupport", setsupport))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("✅ REFLAX Bot চালু!")
    app.run_polling()

if __name__ == "__main__":
    main()
