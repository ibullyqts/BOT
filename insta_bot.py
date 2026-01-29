import os
import time
import random
import threading
from datetime import datetime
from instagrapi import Client

# ================= GITHUB CONFIGURATION =================
SESSION_ID = os.getenv("SESSION_ID")
MY_USERNAME = os.getenv("MY_USERNAME")
MY_ID = str(os.getenv("MY_ID")) 

# PASTE YOUR THREAD ID FROM THE URL LINK HERE
# Example: If link is instagram.com/direct/t/12345/, put "12345"
TARGET_GROUPS = ["340282366841710301281153074832756614682"]

CHECK_SPEED = 12 # Slightly slower for better stability
# ========================================================

cl = Client()
cl.delay_range = [1, 3] 

swipe_active = False
swipe_target_id = None
swipe_messages = [] 
processed_msgs = set()

def login():
    try:
        cl.set_settings({"sessionid": SESSION_ID})
        cl.login_by_sessionid(SESSION_ID)
        print(f"✅ BOT LIVE | Monitoring Thread IDs: {TARGET_GROUPS}")
        return True
    except Exception as e:
        print(f"❌ LOGIN ERROR: {e}")
        return False

def send_msg(thread_id, text, reply_to_id=None):
    try:
        time.sleep(random.uniform(1, 2.5))
        cl.direct_send(text, thread_ids=[thread_id], reply_to_message_id=reply_to_id)
    except Exception as e:
        print(f"⚠️ Message Send Failed: {e}")

def handle_commands(message):
    global swipe_active, swipe_target_id, swipe_messages
    thread_id = str(message.thread_id)
    sender_id = str(message.user_id)
    text = (message.text or "").lower()

    # Log incoming messages for debugging
    print(f"📩 [{thread_id}] {sender_id}: {text}")

    # --- AUTO-SWIPE ---
    if swipe_active and sender_id == swipe_target_id:
        send_msg(thread_id, random.choice(swipe_messages), reply_to_id=message.id)

    # --- ADMIN ONLY ---
    if sender_id != MY_ID: return

    if text.startswith("/swipe "):
        parts = text.split(" ", 2)
        if len(parts) == 3:
            target_username = parts[1].replace("@", "")
            swipe_messages = [m.strip() for m in parts[2].split("|")]
            try:
                swipe_target_id = str(cl.user_id_from_username(target_username))
                swipe_active = True
                send_msg(thread_id, f"🎯 Swiping @{target_username}")
            except: send_msg(thread_id, "❌ User not found")

    elif text == "/stopswipe":
        swipe_active = False
        send_msg(thread_id, "✅ Swipe disabled.")

    elif text == "/ping":
        send_msg(thread_id, "⚡ Bot is alive!")

if __name__ == "__main__":
    if login():
        while True:
            try:
                for t_id in TARGET_GROUPS:
                    # Direct check for new messages in specific thread
                    msgs = cl.direct_messages(t_id, 2)
                    for m in msgs:
                        if m.id not in processed_msgs:
                            threading.Thread(target=handle_commands, args=(m,)).start()
                            processed_msgs.add(m.id)
                
                if len(processed_msgs) > 200: processed_msgs.clear()
                time.sleep(CHECK_SPEED + random.randint(1, 5))
                
            except Exception as e:
                print(f"🔄 Cooling down... Error: {e}")
                time.sleep(60)
