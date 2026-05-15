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

# সেশন ফাইল তৈরি এবং বট কানেক্ট
client = TelegramClient('reflax_bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# --- ২. সোর্স লিস্ট (১৫টি হাই-স্পিড সার্ভার) ---
SOURCES = [
    "https://receive-sms.cc", "https://sms-receive.net", "https://temporary-phone-number.com",
    "https://online-sms.org", "https://receive-smss.com", "https://freephonenum.com",
    "https://smsreceivefree.com", "https://receive-sms-online.info", "https://7sim.net",
    "https://mytrashmobile.com", "https://receive-a-sms.com", "https://sms-online.co",
    "https://getfreesmsnumber.com", "https://sms-man.com/free", "https://receivesms.co"
]

known_numbers = set()

# --- ৩. স্ক্র্যাপিং এবং মনিটর লজিক ---
async def scrape_numbers():
    global known_numbers
    new_finds = []
    for url in SOURCES:
        try:
            res = requests.get(url, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            # বিভিন্ন সাইটের নম্বর ধারণকারী ট্যাগ চেক
            for tag in soup.find_all(['h4', 'div', 'a', 'span']):
                txt = tag.text.strip()
                if txt.startswith('+') and len(txt) > 8:
                    if txt not in known_numbers:
                        known_numbers.add(txt)
                        new_finds.append((txt, url))
        except:
            continue
    return new_finds

async def restock_monitor():
    print("🛰 Initial Scan Started...")
    await scrape_numbers() # শুরুতে সব নম্বর লোড করে নেওয়া
    while True:
        await asyncio.sleep(300) # প্রতি ৫ মিনিট অন্তর চেক করবে
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
            except Exception as e:
                print(f"Error sending alert: {e}")

# --- ৪. বট হ্যান্ডলার্স ---
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    is_admin = event.sender_id in ADMIN_LIST
    status = "🛡 **Admin Mode**" if is_admin else "👤 **User Mode**"
    
    buttons = [
        [Button.inline("🌐 Get Live Number", data="fetch")],
        [Button.url("📢 Join Channel", "https://t.me/REFLAX_1")]
    ]
    
    await event.respond(
        f"🔥 **REFLAX OMNI-STORE v5.0** 🔥\n\n{status}\n"
        f"আমাদের ১৫টি সার্ভার থেকে ওটিপি নিতে নিচের বাটনে ক্লিক করুন।",
        buttons=buttons
    )

@client.on(events.CallbackQuery(data="fetch"))
async def fetch_callback(event):
    nums = list(known_numbers)[-12:] # লেটেস্ট ১২টি নম্বর দেখাবে
    if not nums:
        await event.answer("⏳ সার্ভার স্ক্যান হচ্ছে, ১ মিনিট পর ট্রাই করুন!", alert=True)
        return
    
    buttons = [[Button.inline(f"📲 {n}", data=f"read_{n}")] for n in nums]
    await event.edit("✅ **লেটেস্ট নম্বরসমূহ:**\nওটিপি দেখতে নম্বরে ক্লিক করুন:", buttons=buttons)

@client.on(events.CallbackQuery(data=filter(lambda d: d.startswith(b'read_'))))
async def read_callback(event):
    num = event.data.decode().split('_')[1]
    await event.answer(f"Checking OTP for {num}...", alert=False)
    
    # ওটিপি রিডিং লজিক (উদাহরণস্বরূপ ১নং সার্ভার ব্যবহার করা হয়েছে)
    url = f"https://receive-sms.cc/US-SMS/{num.replace('+', '')}"
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        msg = soup.find('div', class_='col-md-8')
        otp_text = msg.text.strip() if msg else "এখনো কোনো ওটিপি আসেনি। ১ মিনিট পর আবার ট্রাই করুন।"
        
        await event.respond(f"📥 **OTP for** `{num}`:\n\n`{otp_text}`\n\n🤖 @Reflax_Otp_Bot")
    except:
        await event.respond("❌ সার্ভার রেসপন্স দিচ্ছে না। কিছুক্ষণ পর চেষ্টা করুন।")

# --- ৫. মেইন রানার ---
if __name__ == "__main__":
    keep_alive() # Render/Koyeb এ সচল রাখার জন্য
    print("✅ REFLAX BOT IS STARTING...")
    client.loop.create_task(restock_monitor())
    client.run_until_disconnected()