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
# ========================================================

cl = Client()
cl.delay_range = [0, 1]

auto_replies = {}
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

def send_msg(thread_id, text):
    global msg_count
    try:
        cl.direct_send(text, thread_ids=[thread_id])
        msg_count += 1
    except:
        pass

def handle_commands(message):
    global auto_replies, spam_active, start_time, msg_count
    thread_id = message.thread_id
    
    # --- WELCOME & LEAVE DETECTION ---
    if message.item_type == 'action_log':
        event_data = message.event_context
        
        # 1. New Member Added
        if 'user_ids' in event_data:
            for u_id in event_data['user_ids']:
                try:
                    user_info = cl.user_info_v1(u_id)
                    send_msg(thread_id, f"Welcome @{user_info.username}! 🎉 Hope you enjoy the stay. Type /help for my commands.")
                except:
                    send_msg(thread_id, "Welcome to the group! 🎉")
        
        # 2. Member Left or Kicked
        elif 'removed_user_id' in event_data:
            try:
                r_id = event_data['removed_user_id']
                user_info = cl.user_info_v1(r_id)
                send_msg(thread_id, f"Goodbye @{user_info.username}... 🕊️")
            except:
                pass
        return

    # --- TEXT COMMANDS ---
    text = (message.text or "").lower()
    sender_id = str(message.user_id)

    # 1. AUTO-REPLY (Everyone)
    for key, reply in auto_replies.items():
        if key in text:
            send_msg(thread_id, reply)

    # 2. ADMIN-ONLY COMMANDS
    if sender_id != MY_ID:
        return

    if text == "/help":
        menu = (
            "🚀 **INSTANT BOT v3.0**\n\n"
            "🔹 /ping - Check Status\n"
            "🔹 /stats - Uptime & Count\n"
            "🔹 /welcome - Manual Greeting\n"
            "🔹 /funny - Random Joke\n"
            "🔹 /masti - Party Mode\n\n"
            "🛠 **ADMIN TOOLS**\n"
            "🔸 /kick @user - Remove Member\n"
            "🔸 /autoreply [key] [msg]\n"
            "🔸 /stopreply - Clear Keys\n"
            "🔸 /spam @user [msg]\n"
            "🔸 /stopspam - Stop Spamming"
        )
        send_msg(thread_id, menu)

    elif text == "/ping":
        send_msg(thread_id, "⚡ Bot is alive and running on GitHub Actions!")

    elif text == "/stats":
        uptime = str(datetime.now() - start_time).split('.')[0]
        send_msg(thread_id, f"📊 Stats:\nUptime: {uptime}\nTotal Msgs: {msg_count}")

    elif text.startswith("/autoreply "):
        parts = text.split(" ", 2)
        if len(parts) == 3:
            auto_replies[parts[1]] = parts[2]
            send_msg(thread_id, f"✅ Auto-reply set for: {parts[1]}")

    elif text == "/stopreply":
        auto_replies.clear()
        send_msg(thread_id, "🗑 All auto-replies cleared.")

    elif text.startswith("/kick "):
        target = text.split(" ")[1].replace("@", "")
        try:
            t_id = cl.user_id_from_username(target)
            cl.direct_thread_remove_user(thread_id, t_id)
            send_msg(thread_id, f"🚫 Kicked @{target}")
        except Exception as e:
            send_msg(thread_id, f"❌ Failed: {e}")

    elif text == "/funny":
        jokes = ["I told my wife she was drawing her eyebrows too high. She looked surprised.", 
                 "My boss told me to have a good day. So I went home."]
        send_msg(thread_id, random.choice(jokes))

    elif text == "/masti":
        send_msg(thread_id, "🕺💃 Party mode activated! ✨")

if __name__ == "__main__":
    login()
    while True:
        try:
            threads = cl.direct_threads(5)
            for thread in threads:
                # Checking last 3 messages to ensure system events aren't missed
                msgs = cl.direct_messages(thread.id, 3)
                for m in msgs:
                    if m.id not in processed_msgs:
                        threading.Thread(target=handle_commands, args=(m,)).start()
                        processed_msgs.add(m.id)
            
            # Clean up message cache to prevent memory leak
            if len(processed_msgs) > 300:
                processed_msgs.clear()
            
            time.sleep(CHECK_SPEED)
        except Exception as e:
            time.sleep(5)