import os
import time
import random
import datetime
import sys
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# --- CONFIGURATION ---
THREADS = 1             
POLL_INTERVAL = 3       
RESTART_INTERVAL = 1800 # 30 mins
TOTAL_DURATION = 21000  # 6 Hours

# 🤖 COMMAND SETTINGS
SPAM_MESSAGE = "Wake up! 🚨" 
SPAM_BURST_SIZE = 10         
STARTUP_MSG = "🟢 Phoenix Bot is now ONLINE and listening... /help"

# 🛡️ MOD MEMORY
WARN_LOG = {} 

def log_status(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] 🛡️ Mod Bot: {msg}", flush=True)

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def send_message(driver, text):
    try:
        box = driver.find_element(By.XPATH, "//div[@role='textbox'] | //textarea")
        box.click()
        
        driver.execute_script("""
            var el = arguments[0];
            el.focus();
            document.execCommand('insertText', false, arguments[1]);
            el.dispatchEvent(new Event('input', { bubbles: true }));
        """, box, text)
        
        time.sleep(0.1)
        box.send_keys(Keys.ENTER)
        return True
    except:
        return False

def spam_attack(driver):
    log_status("🔥 SPAM MODE ACTIVATED!")
    for i in range(SPAM_BURST_SIZE):
        send_message(driver, f"{SPAM_MESSAGE} {random.randint(1,999)}")
        time.sleep(0.3) 
    log_status("✅ Spam Burst Finished.")

def handle_warn(driver, text):
    try:
        parts = text.split()
        target = "Unknown"
        for word in parts:
            if word.startswith("@"):
                target = word
                break
        
        if target == "Unknown":
            send_message(driver, "⚠️ Syntax Error: Use /warn @username")
            return

        current_strikes = WARN_LOG.get(target, 0) + 1
        WARN_LOG[target] = current_strikes
        
        log_status(f"⚠️ Warning issued to {target} (Strike {current_strikes})")
        
        if current_strikes >= 3:
            send_message(driver, f"🔴 {target} has reached STRIKE 3! Removing user... (Simulation)")
        else:
            send_message(driver, f"⚠️ WARNING: {target} | Strike {current_strikes}/3. Please follow the rules.")
            
    except Exception as e:
        log_status(f"Warn Error: {e}")

def get_last_message(driver):
    try:
        rows = driver.find_elements(By.XPATH, "//div[@role='row']")
        if not rows: return None
        return rows[-1].text.lower()
    except:
        return None

def check_welcomes(driver, last_known_event):
    try:
        events = driver.find_elements(By.XPATH, "//div[contains(text(), 'joined') or contains(text(), 'added')]")
        if events:
            latest = events[-1].text
            if latest != last_known_event:
                user = latest.split(' ')[0]
                log_status(f"🎉 New Member Detected: {user}")
                send_message(driver, f"Welcome {user}! 🌊 Type /help to see commands.")
                return latest
    except:
        pass
    return last_known_event

def run_bot_cycle(cookie, target):
    global_start = time.time()
    last_msg = ""
    last_event = ""

    while (time.time() - global_start) < TOTAL_DURATION:
        driver = None
        try:
            log_status("🚀 Launching Mod Engine...")
            driver = get_driver()
            
            driver.get("https://www.instagram.com/")
            time.sleep(3)
            if "sessionid=" in cookie:
                cookie = cookie.split("sessionid=")[1].split(";")[0].strip()
            driver.add_cookie({'name': 'sessionid', 'value': cookie, 'path': '/', 'domain': '.instagram.com'})
            driver.refresh()
            time.sleep(5)
            
            driver.get(f"https://www.instagram.com/direct/t/{target}/")
            time.sleep(8)
            log_status("✅ Connected. Listening...")

            # 🔔 NOTIFICATION: Send startup message immediately after connecting
            log_status("🔔 Sending Startup Notification...")
            send_message(driver, STARTUP_MSG)

            browser_start = time.time()
            while (time.time() - browser_start) < RESTART_INTERVAL:
                
                # 1. READ COMMANDS
                current_text = get_last_message(driver)
                
                if current_text and current_text != last_msg:
                    if "/spam" in current_text:
                        spam_attack(driver)
                    elif "/warn" in current_text:
                        handle_warn(driver, current_text)
                    elif "/ping" in current_text:
                        send_message(driver, "Pong! 🏓")
                    elif "/help" in current_text:
                        send_message(driver, "⚡ Commands: /spam, /warn @user, /ping")
                    
                    last_msg = current_text
                
                # 2. CHECK WELCOMES
                last_event = check_welcomes(driver, last_event)

                time.sleep(POLL_INTERVAL)

        except Exception as e:
            log_status(f"⚠️ Error: {e}")
            time.sleep(10)
        finally:
            if driver: driver.quit()

def main():
    cookie = os.environ.get("INSTA_COOKIE", "").strip()
    target = os.environ.get("TARGET_THREAD_ID", "").strip()
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(run_bot_cycle, cookie, target)

if __name__ == "__main__":
    main()
