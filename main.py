import asyncio
import requests
from bs4 import BeautifulSoup
from telethon import TelegramClient, events, Button
from keep_alive import keep_alive 

# --- ১. কনফিগারেশন ---
API_ID = 25029252
API_HASH = '2dba1986cb839c95d771ed61a1bcb72e'
BOT_TOKEN = '8907437855:AAHZDxaGe2mvZyXSa1kwGl-4rg_u08yQZmk'
ADMIN_LIST = [6423903661, 6511682794]
OTP_CHANNEL_ID = -1003921715244

client = TelegramClient(None, API_ID, API_HASH).start(bot_token=BOT_TOKEN)
known_numbers = set()

# --- ২. মেইন মেনু বাটন (আপনার ছবির মতো ৬টি বাটন) ---
def get_main_buttons(user_id):
    btns = [
        [Button.inline("📲 Get Number", data="fetch"), Button.inline("🌍 Available Country", data="countries")],
        [Button.inline("✅ Active Numbers", data="active"), Button.inline("☎️ Support", data="support")],
        [Button.inline("📁 Method Files", data="methods"), Button.inline("🛍 Buy IP", data="buy_ip")]
    ]
    if user_id in ADMIN_LIST:
        btns.append([Button.inline("⚙️ Admin Panel", data="admin_panel")])
    return btns

# --- ৩. স্টার্ট কমান্ড ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        "🔥 **WELCOME TO REFLAX OMNI-STORE** 🔥\n\n"
        "সবচেয়ে দ্রুত ওটিপি এবং ফ্রেশ নম্বর পেতে নিচের বাটনগুলো ব্যবহার করুন।",
        buttons=get_main_buttons(event.sender_id)
    )

# --- ৪. বাটন হ্যান্ডলিং (ছবির মতো ওটিপি অপশনসহ) ---
@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()
    user_id = event.sender_id

    # ১. গেট নম্বর (নম্বর লিস্ট)
    if data == "fetch":
        # স্যাম্পল নম্বর (আপনার কোড অনুযায়ী স্ক্র্যাপ হওয়া নম্বর এখানে আসবে)
        nums = ["+9779841005850", "+9779827553900", "+84912345678"]
        buttons = [[Button.inline(f"📲 {n}", data=f"read_{n}")] for n in nums]
        buttons.append([Button.inline("⬅️ Back", data="main_menu")])
        await event.edit("✅ **Select a Number to View OTP:**", buttons=buttons)

    # ২. নম্বর সিলেক্ট করার পর (আপনার ছবির মতো ডিজাইন)
    elif data.startswith("read_"):
        num = data.split('_')[1]
        msg_text = (f"🇳🇵 **Nepal Fresh Number Changed**\n"
                    f"📱 **Platform:** WhatsApp\n\n"
                    f"**Number:** `{num}`\n\n"
                    f"নিচের বাটনে ক্লিক করে ওটিপি দেখুন।")
        
        # আপনার ছবির মতো ৩টি বাটন: View OTP, Change, Back
        panel_buttons = [
            [Button.inline("📩 View OTP", data=f"view_otp_{num}")],
            [Button.inline("🔄 Change Number", data="fetch"), Button.inline("⬅️ Back", data="main_menu")]
        ]
        await event.edit(msg_text, buttons=panel_buttons)

    # ৩. ওটিপি দেখা
    elif data.startswith("view_otp_"):
        await event.answer("⏳ No OTP received yet! Try again in 30 seconds.", alert=True)

    # ৪. এডমিন প্যানেল (শুধুমাত্র আপনার জন্য)
    elif data == "admin_panel":
        if user_id not in ADMIN_LIST:
            await event.answer("❌ আপনি এডমিন নন!", alert=True)
            return
        admin_btns = [
            [Button.inline("📢 Broadcast Message", data="admin_bc")],
            [Button.inline("📊 Scrape Sources", data="admin_src")],
            [Button.inline("⬅️ Back to Main", data="main_menu")]
        ]
        await event.edit("⚙️ **ADMIN CONTROLS v5.0**\nএখানে আপনি বট নিয়ন্ত্রণ করতে পারবেন।", buttons=admin_btns)

    # ৫. মেইন মেনুতে ফিরে যাওয়া
    elif data == "main_menu":
        await event.edit("🔥 **REFLAX OMNI-STORE** 🔥", buttons=get_main_buttons(user_id))

# --- ৫. মেইন রানার ---
if __name__ == "__main__":
    keep_alive() # রেন্ডার অনলাইন রাখতে
    print("🚀 REFLAX BOT IS LIVE WITH ADMIN PANEL!")
    client.run_until_disconnected()
