import os
import time
import random
import threading
from datetime import datetime
from instagrapi import Client

# ================= GITHUB CONFIGURATION =================
SESSION_ID = os.getenv("SESSION_ID")
MY_USERNAME = os.getenv("MY_USERNAME")
MY_ID = str(os.getenv("MY_ID")) # Ensure ID is a string for comparison
CHECK_SPEED = 2 

# Permanent Whitelist (IDs here stay after restart)
AUTHORIZED_GROUPS = [] 
# ========================================================

cl = Client()
cl.delay_range = [0, 1]

# Global State
auto_replies = {}
swipe_active = False
swipe_target_id = None
swipe_messages = [] 
spam_active = False
start_time = datetime.now()
msg_count = 0
processed_msgs = set()

def login():
    try:
        if not SESSION_ID:
            print("❌ ERROR: SESSION_ID secret is missing!")
            return False
        cl.set_settings({"sessionid": SESSION_ID})
        cl.login_by_sessionid(SESSION_ID)
        print(f"✅ LOGIN SUCCESS | Logged in as: {cl.account_info().username}")
        print(f"👑 Admin ID Set to: {MY_ID}")
        return True
    except Exception as e:
        print(f"❌ LOGIN FAILED: {e}")
        print("💡 TIP: Check if your Session ID is expired or if Instagram is asking for 2FA.")
        return False

def send_msg(thread_id, text, reply_to_id=None):
    global msg_count
    try:
        cl.direct_send(text, thread_ids=[thread_id], reply_to_message_id=reply_to_id)
        msg_count += 1
    except Exception as e:
        print(f"⚠️ Failed to send message: {e}")

def handle_commands(message):
    global auto_replies, swipe_active, swipe_target_id, swipe_messages, AUTHORIZED_GROUPS
    thread_id = str(message.thread_id)
    sender_id = str(message.user_id)
    text = (message.text or "").lower()

    # DEBUG LOG: Shows every message the bot sees in the GitHub terminal
    print(f"📩 Msg from {sender_id} in {thread_id}: {text}")

    # --- ADMIN AUTHORIZATION ---
    if sender_id == MY_ID:
        if text == "/authorize":
            if thread_id not in AUTHORIZED_GROUPS:
                AUTHORIZED_GROUPS.append(thread_id)
                send_msg(thread_id, f"✅ AUTHORIZED: {thread_id}")
            return
        elif text == "/deauthorize":
            if thread_id in AUTHORIZED_GROUPS:
                AUTHORIZED_GROUPS.remove(thread_id)
                send_msg(thread_id, "🛑 DEAUTHORIZED.")
            return

    # Filter: Only work in authorized groups
    if thread_id not in AUTHORIZED_GROUPS:
        return

    # --- AUTO-SWIPE LOGIC ---
    if swipe_active and sender_id == swipe_target_id:
        random_reply = random.choice(swipe_messages)
        send_msg(thread_id, random_reply, reply_to_id=message.id)

    # --- ADMIN COMMANDS ---
    if sender_id != MY_ID:
        return

    if text.startswith("/swipe "):
        parts = text.split(" ", 2)
        if len(parts) == 3:
            target_username = parts[1].replace("@", "")
            swipe_messages = [m.strip() for m in parts[2].split("|")]
            try:
                swipe_target_id = str(cl.user_id_from_username(target_username))
                swipe_active = True
                send_msg(thread_id, f"🎯 Swiping @{target_username} with {len(swipe_messages)} variants.")
            except Exception as e:
                send_msg(thread_id, f"❌ User lookup failed: {e}")

    elif text == "/stopswipe":
        swipe_active = False
        send_msg(thread_id, "✅ Swipe disabled.")

    elif text.startswith("/kick "):
        target = text.split(" ")[1].replace("@", "")
        try:
            t_id = cl.user_id_from_username(target)
            cl.direct_thread_remove_user(thread_id, t_id)
            send_msg(thread_id, f"🚫 Kicked @{target}")
        except Exception as e:
            send_msg(thread_id, f"❌ Kick Failed: {e}")

    elif text == "/ping":
        send_msg(thread_id, "⚡ Bot is Online & Active!")

    elif text == "/help":
        menu = "🤖 **BOT v4.7**\n/ping, /authorize, /kick @user, /swipe @user msg1|msg2, /stopswipe"
        send_msg(thread_id, menu)

# ================= MAIN LOOP =================
if __name__ == "__main__":
    if login():
        while True:
            try:
                # Check top 10 threads
                threads = cl.direct_threads(10)
                for thread in threads:
                    msgs = cl.direct_messages(thread.id, 3)
                    for m in msgs:
                        if m.id not in processed_msgs:
                            threading.Thread(target=handle_commands, args=(m,)).start()
                            processed_msgs.add(m.id)
                
                # Prevent memory buildup
                if len(processed_msgs) > 500: processed_msgs.clear()
                
                time.sleep(CHECK_SPEED)
            except Exception as e:
                print(f"🔄 Loop Warning: {e}")
                time.sleep(5)
    else:
        print("‼️ Bot could not start due to login failure.")
