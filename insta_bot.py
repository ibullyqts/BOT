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

def login():
    try:
        if not SESSION_ID:
            print("❌ ERROR: SESSION_ID secret is missing!")
            return False
        
        # MANUAL BYPASS: Directly injecting the session cookie
        # This avoids the broken 'pinned_channels_info' logic in instagrapi
        cl.set_settings({"sessionid": SESSION_ID})
        
        # We manually set the authorization headers
        cl.authorization = {
            "sessionid": SESSION_ID,
        }
        
        # Verify the session works by getting a tiny bit of data
        # If this doesn't crash, we are successfully logged in
        cl.get_timeline_feed() 
        
        print(f"✅ MANUAL LOGIN SUCCESS | {datetime.now().strftime('%H:%M:%S')}")
        return True
    except Exception as e:
        print(f"⚠️ Manual Injection Warning: {e}")
        # Even if a small check fails, we try to proceed
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

    # Swipe Logic
    if swipe_active and sender_id == swipe_target_id:
        try:
            time.sleep(random.uniform(1.5, 3.5))
            cl.direct_send(random.choice(swipe_messages), thread_ids=[thread_id], reply_to_message_id=message.id)
            print(f"🎯 Swiped @{sender_id}")
        except: pass

    # Admin Commands
    if sender_id == MY_ID:
        if text.startswith("/swipe "):
            parts = text.split(" ", 2)
            if len(parts) == 3:
                target_username = parts[1].replace("@", "")
                swipe_messages = [m.strip() for m in parts[2].split("|")]
                try:
                    swipe_target_id = str(cl.user_id_from_username(target_username))
                    swipe_active = True
                    cl.direct_send(f"🎯 Target set: @{target_username}", thread_ids=[thread_id])
                except: pass
        elif text == "/stopswipe":
            swipe_active = False
            cl.direct_send("✅ Swipe disabled.", thread_ids=[thread_id])

if __name__ == "__main__":
    if login():
        print("🚀 Monitoring specific threads...")
        while True:
            try:
                for t_id in TARGET_GROUPS:
                    # Fetch messages directly by thread ID
                    msgs = cl.direct_messages(t_id, 2)
                    for m in msgs:
                        if m.id not in processed_msgs:
                            threading.Thread(target=handle_commands, args=(m,)).start()
                            processed_msgs.add(m.id)
                
                if len(processed_msgs) > 200: processed_msgs.clear()
                
                # Sleep with jitter
                time.sleep(CHECK_SPEED + random.randint(1, 5))
                
            except Exception as e:
                # If we hit the 'pinned_channels' error here, we just ignore it
                if "pinned_channels_info" in str(e):
                    time.sleep(CHECK_SPEED)
                    continue
                print(f"🔄 Loop Warning: {e}")
                time.sleep(60) 
    else:
        print("‼️ Could not establish session.")
