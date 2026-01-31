import os
import time
import re
import random
import datetime
import sys
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

# --- MOD BOT CONFIGURATION ---
THREADS = 1             # Listeners must be single-threaded per group
POLL_INTERVAL = 5       # Check for new messages every 5 seconds
RESTART_INTERVAL = 1800 # Restart browser every 30 mins (RAM Safety)
TOTAL_DURATION = 21000  # 6 Hours total runtime

# 🤖 BOT SETTINGS
BOT_PREFIX = "/"
ADMIN_USERS = ["your_username", "admin_friend"] # Users allowed to use admin commands

def log_status(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] 🛡️ Mod Bot: {msg}", flush=True)

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") # Set to False if debugging locally
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Block images to speed up "Reading" speed
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Anti-Detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def send_message(driver, text):
    """Injects text into the chat box and sends it."""
    try:
        # Find box using robust XPath (looks for "Message..." placeholder or textbox role)
        box = driver.find_element(By.XPATH, "//div[@role='textbox'] | //textarea")
        box.click()
        
        # JS Injection for speed and reliability
        driver.execute_script("""
            var el = arguments[0];
            el.focus();
            document.execCommand('insertText', false, arguments[1]);
            el.dispatchEvent(new Event('input', { bubbles: true }));
        """, box, text)
        
        time.sleep(0.5)
        box.send_keys(Keys.ENTER)
        log_status(f"Sent: {text}")
        return True
    except Exception as e:
        log_status(f"❌ Send Failed: {e}")
        return False

def get_last_message(driver):
    """
    Scrapes the chat to find the very last message bubble.
    Returns: (text, author_name)
    """
    try:
        # This XPath finds all message rows
        rows = driver.find_elements(By.XPATH, "//div[@role='row']")
        if not rows: return None, None
        
        # Get the very last row
        last_row = rows[-1]
        text = last_row.text
        
        # Simple extraction (Instagram groups usually show name above text)
        # We perform a basic split to separate name from content
        lines = text.split('\n')
        if len(lines) >= 1:
            return lines[-1], lines[0] # content, potential_author
        return text, "Unknown"
    except:
        return None, None

def check_for_system_events(driver, last_known_text):
    """
    Checks for 'User joined the group' messages.
    """
    try:
        # Look for gray system text containing keywords
        # Instagram classes change, but the text usually stays standard
        events = driver.find_elements(By.XPATH, "//div[contains(text(), 'added') or contains(text(), 'joined') or contains(text(), 'left')]")
        
        if events:
            latest_event = events[-1].text
            if latest_event != last_known_text:
                if "added" in latest_event or "joined" in latest_event:
                    # Extract name roughly
                    new_user = latest_event.split(' ')[0]
                    send_message(driver, f"Welcome {new_user}! Please read the rules with /rules 🛡️")
                    return latest_event
    except:
        pass
    return last_known_text

def process_commands(driver, text):
    """
    The Brain: Decides what to do with a command.
    """
    cmd = text.lower().strip()
    
    if cmd == "/ping":
        send_message(driver, "Pong! 🏓 (Bot is Online)")
    
    elif cmd == "/help":
        send_message(driver, "🤖 Commands: /ping, /rules, /admin")
        
    elif cmd == "/rules":
        send_message(driver, "📜 Rules:\n1. No Spam\n2. Be Respectful\n3. No NSFW")
        
    elif cmd == "/admin":
        send_message(driver, "👑 Admin contact: @YourNameHere")

    elif cmd.startswith("/warn"):
        # Example: /warn @user
        target = text.split(" ")[-1]
        send_message(driver, f"⚠️ WARNING issued to {target}. Next strike is a ban.")

def run_bot_cycle(cookie, target):
    global_start_time = time.time()
    last_processed_msg = ""
    last_system_event = ""

    while (time.time() - global_start_time) < TOTAL_DURATION:
        driver = None
        try:
            log_status("🚀 Launching Mod Listener...")
            driver = get_driver()
            
            # Login
            driver.get("https://www.instagram.com/")
            time.sleep(3)
            
            if "sessionid=" in cookie:
                cookie_val = cookie.split("sessionid=")[1].split(";")[0].strip()
            else:
                cookie_val = cookie.strip()
                
            driver.add_cookie({'name': 'sessionid', 'value': cookie_val, 'path': '/', 'domain': '.instagram.com'})
            driver.refresh()
            time.sleep(5)
            
            # Go to specific Group Chat
            driver.get(f"https://www.instagram.com/direct/t/{target}/")
            time.sleep(8)
            log_status("✅ Connected to Group Chat. Listening...")

            # 👂 LISTENING LOOP (Refreshing browser every 30m)
            browser_start = time.time()
            while (time.time() - browser_start) < RESTART_INTERVAL:
                
                # 1. Check for User Commands
                current_text, author = get_last_message(driver)
                
                if current_text and current_text != last_processed_msg:
                    # It's a new message!
                    if current_text.startswith(BOT_PREFIX):
                        log_status(f"Command Detected from {author}: {current_text}")
                        process_commands(driver, current_text)
                    
                    last_processed_msg = current_text
                
                # 2. Check for System Events (Welcomes)
                new_event = check_for_system_events(driver, last_system_event)
                if new_event != last_system_event:
                    last_system_event = new_event

                time.sleep(POLL_INTERVAL)

        except Exception as e:
            log_status(f"⚠️ Error: {e}")
            time.sleep(10)
        finally:
            if driver: driver.quit()

def main():
    cookie = os.environ.get("INSTA_COOKIE", "").strip()
    target = os.environ.get("TARGET_THREAD_ID", "").strip()
    
    if not cookie or not target:
        print("❌ Missing Secrets!")
        sys.exit(1)

    # Single Thread for Logic (Multi-thread listener causes race conditions)
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(run_bot_cycle, cookie, target)

if __name__ == "__main__":
    main()
