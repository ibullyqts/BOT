import os
import time
import random
import threading
from datetime import datetime
from instagrapi import Client

# ================= GITHUB CONFIGURATION =================
SESSION_ID = os.getenv("SESSION_ID")
MY_USERNAME = os.getenv("MY_USERNAME")
MY_ID = os.getenv("MY_ID") 
CHECK_SPEED = 2 
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
        cl.set_settings({"sessionid": SESSION_ID})
        cl.login_by_sessionid(SESSION_ID)
        print(f"🚀 Bot Running | Admin ID: {MY_ID}")
    except Exception as e:
        print(f"❌ Login Failed: {e}")
        exit()

def send_msg(thread_id, text, reply_to_id=None):
    global msg_count
    try:
        cl.direct_send(text, thread_ids=[thread_id], reply_to_message_id=reply_to_id)
        msg_count += 1
    except:
        pass

def handle_commands(message):
    global auto_replies, swipe_active, swipe_target_id, swipe_messages, AUTHORIZED_GROUPS
    thread_id = str(message.thread_id)
    sender_id = str(message.user_id)
    text = (message.text or "").lower()

    # --- ADMIN AUTHORIZATION ---
    if sender_id == MY_ID:
        if text == "/authorize":
            if thread_id not in AUTHORIZED_GROUPS:
                AUTHORIZED_GROUPS.append(thread_id)
                send_msg(thread_id, f"✅ Authorized Group: {thread_id}")
            return
        elif text == "/deauthorize":
            if thread_id in AUTHORIZED_GROUPS:
                AUTHORIZED_GROUPS.remove(thread_id)
                send_msg(thread_id, "🛑 Deauthorized.")
            return

    if thread_id not in AUTHORIZED_GROUPS:
        return

    # --- RANDOM AUTO-SWIPE LOGIC ---
    if swipe_active and sender_id == swipe_target_id:
        random_reply = random.choice(swipe_messages)
        send_msg(thread_id, random_reply, reply_to_id=message.id)

    # --- ADMIN COMMANDS ---
    if sender_id != MY_ID:
        return

    # /swipe @user msg1 | msg2
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
            # FIXED: Updated to the correct current function name
            cl.direct_thread_remove_user(thread_id, t_id)
            send_msg(thread_id, f"🚫 Kicked @{target}")
        except Exception as e:
            send_msg(thread_id, f"❌ Kick Failed: {str(e)}")

    elif text == "/help":
        menu = (
            "🤖 **PREMIUM BOT v4.6**\n\n"
            "🔹 /swipe @user msg1 | msg2 - Random replies\n"
            "🔹 /kick @user - Remove user\n"
            "🔹 /authorize - Enable group\n"
            "🔹 /ping - Status"
        )
        send_msg(thread_id, menu)

    elif text == "/ping":
        send_msg(thread_id, "⚡ Active.")

# ================= MAIN LOOP =================
if __name__ == "__main__":
    login()
    while True:
        try:
            threads = cl.direct_threads(10)
            for thread in threads:
                msgs = cl.direct_messages(thread.id, 3)
                for m in msgs:
                    if m.id not in processed_msgs:
                        threading.Thread(target=handle_commands, args=(m,)).start()
                        processed_msgs.add(m.id)
            if len(processed_msgs) > 300: processed_msgs.clear()
            time.sleep(CHECK_SPEED)
        except Exception as e:
            time.sleep(5)
