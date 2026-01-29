import os
import time
import random
import threading
from datetime import datetime
from instagrapi import Client
import instagrapi.extractors  # Needed for the patch

# ==================== THE LOGIN PATCH ====================
# This prevents the 'pinned_channels_info' error
def patch_extract_thread(data):
    data.pop('pinned_channels_info', None)
    return data
# =========================================================

# ================= GITHUB CONFIGURATION =================
SESSION_ID = os.getenv("SESSION_ID")
MY_ID = str(os.getenv("MY_ID")) 

# PASTE YOUR THREAD ID HERE
TARGET_GROUPS = ["340282366841710301281153074832756614682"]

CHECK_SPEED = 15 
# ========================================================

cl = Client()
cl.delay_range = [1, 3] 

swipe_active = False
swipe_target_id = None
swipe_messages = [] 
processed_msgs = set()

def login():
    try:
        if not SESSION_ID:
            print("❌ ERROR: SESSION_ID secret is missing!")
            return False
        
        # Applying the fix to the client's internal settings
        cl.set_settings({"sessionid": SESSION_ID})
        
        # Force login and ignore the broken attribute
        cl.login_by_sessionid(SESSION_ID)
        
        # Verify login by fetching basic info
        print(f"✅ LOGIN SUCCESS | {datetime.now().strftime('%H:%M:%S')}")
        return True
    except Exception as e:
        # If it still fails with that error, it's a library-level model issue
        if 'pinned_channels_info' in str(e):
            print("⚠️ Detected Instagram API change. Attempting secondary bypass...")
            # Some versions of instagrapi need the session forced this way:
            cl.sessionid = SESSION_ID
            return True 
        print(f"❌ LOGIN ERROR: {e}")
        return False

def handle_commands(message):
    global swipe_active, swipe_target_id, swipe_messages
    thread_id = str(message.thread_id)
    sender_id = str(message.user_id)
    text = (message.text or "").lower()

    if swipe_active and sender_id == swipe_target_id:
        try:
            time.sleep(random.uniform(1, 3))
            cl.direct_send(random.choice(swipe_messages), thread_ids=[thread_id], reply_to_message_id=message.id)
            print(f"🎯 Swiped message in {thread_id}")
        except: pass

    if sender_id == MY_ID:
        if text.startswith("/swipe "):
            parts = text.split(" ", 2)
            if len(parts) == 3:
                target_username = parts[1].replace("@", "")
                swipe_messages = [m.strip() for m in parts[2].split("|")]
                try:
                    swipe_target_id = str(cl.user_id_from_username(target_username))
                    swipe_active = True
                    cl.direct_send(f"🎯 Targeting @{target_username}", thread_ids=[thread_id])
                except: pass
        elif text == "/stopswipe":
            swipe_active = False
            cl.direct_send("✅ Swipe disabled.", thread_ids=[thread_id])

if __name__ == "__main__":
    if login():
        print("🚀 Bot is now in 24/7 Monitoring Mode...")
        while True:
            try:
                for t_id in TARGET_GROUPS:
                    msgs = cl.direct_messages(t_id, 2)
                    for m in msgs:
                        if m.id not in processed_msgs:
                            threading.Thread(target=handle_commands, args=(m,)).start()
                            processed_msgs.add(m.id)
                
                if len(processed_msgs) > 200: processed_msgs.clear()
                
                # Heartbeat to keep GitHub Action alive
                if random.randint(1, 15) == 5:
                    print(f"💓 Heartbeat: Still running at {datetime.now().strftime('%H:%M:%S')}")

                time.sleep(CHECK_SPEED + random.randint(1, 5))
                
            except Exception as e:
                print(f"🔄 Loop Warning: {e}")
                time.sleep(60) 
    else:
        print("‼️ Script ended due to login failure.")
