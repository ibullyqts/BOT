import os
import time
import random
import threading
from datetime import datetime
from instagrapi import Client

# ================= GITHUB CONFIGURATION =================
SESSION_ID = os.getenv("SESSION_ID")
MY_ID = str(os.getenv("MY_ID")) 

# PASTE YOUR THREAD ID HERE
TARGET_GROUPS = ["340282366841710301281153074832756614682"]

CHECK_SPEED = 15 
# ========================================================

cl = Client()

def log(message):
    """Helper to print logs with timestamps."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def login():
    try:
        if not SESSION_ID:
            log("❌ ERROR: SESSION_ID secret is missing!")
            return False
        
        # Manual Session Injection to bypass broken 'pinned_channels' logic
        cl.set_settings({"sessionid": SESSION_ID})
        cl.authorization = {"sessionid": SESSION_ID}
        
        # We test the connection with a simple request
        cl.get_timeline_feed() 
        log("✅ LOGIN SUCCESSful via Manual Injection.")
        return True
    except Exception as e:
        log(f"⚠️ Login Warning: {e}")
        # We return True anyway to try and start the loop
        return True 

swipe_active = False
swipe_target_id = None
swipe_messages = [] 
processed_msgs = set()

def handle_commands(message):
    global swipe_active, swipe_target_id, swipe_messages
    thread_id = str(message.thread_id)
    sender_id = str(message.user_id)
    text = (message.text or "").lower()

    # Log incoming messages
    log(f"📩 Incoming from {sender_id}: '{text}'")

    if swipe_active and sender_id == swipe_target_id:
        try:
            time.sleep(random.uniform(1.5, 3.5))
            cl.direct_send(random.choice(swipe_messages), thread_ids=[thread_id], reply_to_message_id=message.id)
            log(f"🎯 Successfully Swiped @{sender_id}")
        except Exception as e:
            log(f"⚠️ Swipe Failed: {e}")

    if sender_id == MY_ID:
        if text.startswith("/swipe "):
            parts = text.split(" ", 2)
            if len(parts) == 3:
                target_username = parts[1].replace("@", "")
                swipe_messages = [m.strip() for m in parts[2].split("|")]
                try:
                    swipe_target_id = str(cl.user_id_from_username(target_username))
                    swipe_active = True
                    cl.direct_send(f"🎯 Target Locked: @{target_username}", thread_ids=[thread_id])
                    log(f"🚀 Admin Command: Target set to @{target_username}")
                except Exception as e:
                    log(f"❌ User lookup error: {e}")
        elif text == "/stopswipe":
            swipe_active = False
            cl.direct_send("✅ Swipe disabled.", thread_ids=[thread_id])
            log("🛑 Admin Command: Swipe Disabled.")

if __name__ == "__main__":
    log("🏁 Starting Bot Execution...")
    if login():
        log(f"👀 Monitoring {len(TARGET_GROUPS)} thread(s)...")
        while True:
            try:
                for t_id in TARGET_GROUPS:
                    # Fetching 2 messages at a time
                    try:
                        msgs = cl.direct_messages(t_id, 2)
                    except Exception as e:
                        if "pinned_channels_info" in str(e):
                            continue # Ignore the library model crash
                        log(f"⚠️ Error fetching {t_id}: {e}")
                        continue

                    for m in msgs:
                        if m.id not in processed_msgs:
                            threading.Thread(target=handle_commands, args=(m,)).start()
                            processed_msgs.add(m.id)
                
                if len(processed_msgs) > 200: 
                    processed_msgs.clear()
                    log("🧹 Cache Cleared.")
                
                time.sleep(CHECK_SPEED + random.randint(1, 5))
                
            except Exception as e:
                log(f"🔄 Loop Exception: {e}")
                time.sleep(60) 
    else:
        log("‼️ Bot terminated: Could not establish session.")
