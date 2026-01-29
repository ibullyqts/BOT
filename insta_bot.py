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

# PASTE YOUR GROUP IDS HERE (Must be strings in the list)
TARGET_GROUPS = ["PASTE_YOUR_ID_HERE"]

CHECK_SPEED = 10 
# ========================================================

cl = Client()
cl.delay_range = [1, 3] 

auto_replies = {}
swipe_active = False
swipe_target_id = None
swipe_messages = [] 
start_time = datetime.now()
msg_count = 0
processed_msgs = set()

def login():
    try:
        cl.set_settings({"sessionid": SESSION_ID})
        cl.login_by_sessionid(SESSION_ID)
        print(f"✅ LOGIN SUCCESS | Active in {len(TARGET_GROUPS)} groups.")
        return True
    except Exception as e:
        print(f"❌ LOGIN FAILED: {e}")
        return False

def send_msg(thread_id, text, reply_to_id=None):
    global msg_count
    try:
        time.sleep(random.uniform(1, 2))
        cl.direct_send(text, thread_ids=[thread_id], reply_to_message_id=reply_to_id)
        msg_count += 1
    except Exception as e:
        print(f"⚠️ Send Error: {e}")

def handle_commands(message):
    global auto_replies, swipe_active, swipe_target_id, swipe_messages
    thread_id = str(message.thread_id)
    sender_id = str(message.user_id)
    text = (message.text or "").lower()

    print(f"📩 [{thread_id}] {sender_id}: {text}")

    if swipe_active and sender_id == swipe_target_id:
        send_msg(thread_id, random.choice(swipe_messages), reply_to_id=message.id)

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
        send_msg(thread_id, "⚡ Bot is alive and direct-monitoring!")

if __name__ == "__main__":
    if login():
        while True:
            try:
                for thread_id in TARGET_GROUPS:
                    msgs = cl.direct_messages(thread_id, 2)
                    for m in msgs:
                        if m.id not in processed_msgs:
                            threading.Thread(target=handle_commands, args=(m,)).start()
                            processed_msgs.add(m.id)
                
                if len(processed_msgs) > 200: processed_msgs.clear()
                
                time.sleep(CHECK_SPEED + random.uniform(2, 5))
                
            except Exception as e:
                print(f"🔄 Direct Scan Warning: {e}")
                time.sleep(60) # Line 104 fixed here
    else:
        print("‼️ Stop: Fix Login.")
