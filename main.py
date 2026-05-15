import asyncio
import requests
from bs4 import BeautifulSoup
from telethon import TelegramClient, events, Button
from keep_alive import keep_alive 

# --- ১. ক্রেডেনশিয়ালস সেটআপ ---
API_ID = 25029252
API_HASH = '2dba1986cb839c95d771ed61a1bcb72e'
BOT_TOKEN = '8907437855:AAHZDxaGe2mvZyXSa1kwGl-4rg_u08yQZmk'
ADMIN_LIST = [6423903661, 6511682794]
OTP_CHANNEL_ID = -1003921715244

# সেশন ফাইল 'None' করা হয়েছে যাতে Render-এ কোনো ফাইল রাইট এরর না আসে
client = TelegramClient(None, API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ১৫টি ওটিপি সার্ভার সোর্স
SOURCES = [
    "https://receive-sms.cc", "https://sms-receive.net", "https://temporary-phone-number.com",
    "https://online-sms.org", "https://receive-smss.com", "https://freephonenum.com",
    "https://smsreceivefree.com", "https://receive-sms-online.info", "https://7sim.net",
    "https://mytrashmobile.com", "https://receive-a-sms.com", "https://sms-online.co",
    "https://getfreesmsnumber.com", "https://sms-man.com/free", "https://receivesms.co"
]

known_numbers = set()

# --- ২. নম্বর স্ক্র্যাপিং ফাংশন ---
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
        except:
            continue
    return new_finds

# --- ৩. অটো মনিটর (রিস্টক এলার্ট) ---
async def restock_monitor():
    await scrape_numbers() # শুরুতে সব লোড হবে
    while True:
        await asyncio.sleep(300) # প্রতি ৫ মিনিট পর পর চেক
        new_list = await scrape_numbers()
        for num, src in new_list:
            alert = (f"🚨 **RESTOCK ALERT!**\n"
                     f"━━━━━━━━━━━━━━━━━━━━\n"
                     f"📲 **Number:** `{num}`\n"
                     f"📡 **Source:** Server_Reflax\n"
                     f"✅ **Status:** Active\n"
                     f"━━━━━━━━━━━━━━━━━━━━\n"
                     f"🤖 @Reflax_Otp_Bot")
            try:
                await client.send_message(OTP_CHANNEL_ID, alert)
            except:
                pass

# --- ৪. বট কমান্ড হ্যান্ডলার্স ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    buttons = [
        [Button.inline("🌐 Get Live Number", data="fetch")],
        [Button.url("📢 Join Channel", "https://t.me/REFLAX_1")]
    ]
    await event.respond(
        "🔥 **REFLAX OMNI-STORE v5.0** 🔥\n\n"
        "সবচেয়ে দ্রুত ওটিপি সার্ভিস পেতে নিচের বাটনে ক্লিক করুন।",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data="fetch"))
async def fetch_callback(event):
    nums = list(known_numbers)[-12:] # শেষ ১২টি নম্বর দেখাবে
    if not nums:
        await event.answer("⏳ সার্ভার স্ক্যান হচ্ছে, ১ মিনিট পর ট্রাই করুন!", alert=True)
        return
    
    buttons = [[Button.inline(f"📲 {n}", data=f"read_{n}")] for n in nums]
    await event.edit("✅ **লেটেস্ট নম্বরসমূহ:**\nওটিপি দেখতে নম্বরে ক্লিক করুন:", buttons=buttons)

# এখানে প্যাটার্ন ফিক্স করা হয়েছে (Error fix)
@client.on(events.CallbackQuery(pattern=rb'read_.*'))
async def read_callback(event):
    num_val = event.data.decode().split('_')[1]
    await event.answer(f"Checking OTP for {num_val}...", alert=False)
    
    # সিম্পল ওটিপি রেসপন্স
    await event.respond(
        f"📥 **OTP for** `{num_val}`:\n\n"
        f"এখনো কোনো ওটিপি আসেনি। ১-২ মিনিট অপেক্ষা করে আবার ট্রাই করুন।\n\n"
        f"🤖 @Reflax_Otp_Bot"
    )

# --- ৫. মেইন রানার ---
if __name__ == "__main__":
    keep_alive() # Render-এ সচল রাখতে
    print("🚀 REFLAX BOT IS STARTING...")
    client.loop.create_task(restock_monitor())
    client.run_until_disconnected()
