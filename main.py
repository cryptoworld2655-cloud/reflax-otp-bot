import asyncio
import requests
from bs4 import BeautifulSoup
from telethon import TelegramClient, events, Button
from keep_alive import keep_alive 

# --- ১. কনফিগারেশন ---
API_ID = 25029252
API_HASH = '2dba1986cb839c95d771ed61a1bcb72e'
BOT_TOKEN = '8907437855:AAHZDxaGe2mvZyXSa1kwGl-4rg_u08yQZmk'
ADMIN_LIST = [6423903661, 6511682794] # এখানে আপনার আইডি আছে
OTP_CHANNEL_ID = -1003921715244

client = TelegramClient(None, API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ওটিপি সোর্স লিস্ট
SOURCES = ["https://receive-sms.cc", "https://sms-receive.net", "https://online-sms.org"]
known_numbers = set()

# --- ২. ব্যাকএন্ড ফাংশন ---
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

# --- ৩. মেইন মেনু (User Interface) ---
def get_main_buttons(user_id):
    btns = [
        [Button.inline("📲 Get Number", data="fetch"), Button.inline("🌍 Available Country", data="countries")],
        [Button.inline("✅ Active Numbers", data="active"), Button.inline("☎️ Support", data="support")],
        [Button.inline("📁 Method Files", data="methods"), Button.inline("🛍 Buy IP", data="buy_ip")]
    ]
    # যদি ইউজার এডমিন হয়, তবে এডমিন প্যানেল বাটন দেখাবে
    if user_id in ADMIN_LIST:
        btns.append([Button.inline("⚙️ Admin Panel", data="admin_panel")])
    return btns

# --- ৪. কমান্ড হ্যান্ডলার্স ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        "🔥 **WELCOME TO REFLAX OMNI-STORE** 🔥\n\n"
        "আপনার পছন্দের অপশনটি নিচের বাটন থেকে সিলেক্ট করুন।",
        buttons=get_main_buttons(event.sender_id)
    )

# --- ৫. বাটন অ্যাকশন (Callback Queries) ---
@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()
    
    if data == "fetch":
        nums = list(known_numbers)[-10:]
        if not nums:
            await event.answer("⏳ No numbers found. Scanning...", alert=True)
            return
        buttons = [[Button.inline(f"📲 {n}", data=f"read_{n}")] for n in nums]
        buttons.append([Button.inline("⬅️ Back", data="main_menu")])
        await event.edit("✅ **Available Numbers:**", buttons=buttons)

    elif data == "admin_panel":
        if event.sender_id not in ADMIN_LIST:
            await event.answer("❌ Access Denied!", alert=True)
            return
        admin_btns = [
            [Button.inline("📢 Broadcast Msg", data="broadcast")],
            [Button.inline("📊 Scrape Sources", data="view_sources")],
            [Button.inline("⬅️ Main Menu", data="main_menu")]
        ]
        await event.edit("⚙️ **ADMIN CONTROLS v5.0**", buttons=admin_btns)

    elif data == "support":
        await event.edit("☎️ **Contact Support:** @REFLAX_1\nযেকোনো সমস্যায় আমাদের নক দিন।", 
                         buttons=[Button.inline("⬅️ Back", data="main_menu")])

    elif data == "main_menu":
        await event.edit("🔥 **REFLAX OMNI-STORE** 🔥", buttons=get_main_buttons(event.sender_id))

    elif data.startswith("read_"):
        num = data.split('_')[1]
        await event.respond(f"📩 **OTP for {num}:**\n\nNo OTP received yet. Wait 2 minutes.")

# --- ৬. অটো রিস্টক এলার্ট ---
async def restock_monitor():
    await scrape_numbers()
    while True:
        await asyncio.sleep(300)
        new_list = await scrape_numbers()
        for num, src in new_list:
            alert = f"🚨 **RESTOCK ALERT!**\n📲 **Number:** `{num}`\n🤖 @Reflax_Otp_Bot"
            try: await client.send_message(OTP_CHANNEL_ID, alert)
            except: pass

if __name__ == "__main__":
    keep_alive()
    print("🚀 Reflax Bot Started!")
    client.loop.create_task(restock_monitor())
    client.run_until_disconnected()
