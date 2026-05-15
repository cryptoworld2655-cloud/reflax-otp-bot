from flask import Flask
from threading import Thread

# Flask অ্যাপ তৈরি
app = Flask('')

@app.route('/')
def home():
    # এটি ব্রাউজারে দেখা যাবে যখন আপনি লিংকে ভিজিট করবেন
    return "REFLAX OTP BOT IS ALIVE!"

def run():
    # পোর্ট ৮০৮০ তে সার্ভার রান করবে
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # আলাদা থ্রেডে সার্ভারটি চালু করা যাতে বটের মেইন কোড ডিস্টার্ব না হয়
    t = Thread(target=run)
    t.start()