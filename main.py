import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import requests
import traceback

# --- CONFIG ---
USERNAME = 'username_here'
PASSWORD = 'password_here'
TARGET_USERNAME = 'target_profile_here'
DISCORD_WEBHOOK_URL = 'discord_webhook_url_here'  
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(BASE_DIR, "last_status.json")
LOG_FILE = os.path.join(BASE_DIR, "log.txt")

def log_message(message):
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(message + "\n")
    print(message)

try:
    log_message("🚀 Script started")

    options = Options()
    options.add_argument("--headless=new")   
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

   
    driver.get("https://www.instagram.com/")
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, 'username'))).send_keys(USERNAME)
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.NAME, 'password'))).send_keys(PASSWORD)
    WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="loginForm"]/div/div[3]/button'))).click()
    sleep(8)

    
    driver.get(f"https://www.instagram.com/{TARGET_USERNAME}/")
    sleep(5)

   
    counts = WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.XPATH, "//header//ul/li"))
    )

    def clean_count(text):
        return text.split("\n")[0].replace(",", "").replace(".", "")

    posts = clean_count(counts[0].text)
    followers = clean_count(counts[1].text)
    following = clean_count(counts[2].text)

    current_data = {
        "posts": posts,
        "followers": followers,
        "following": following
    }


    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            last_data = json.load(f)
    else:
        last_data = {}

    changes = {}
    for key in current_data:
        if str(current_data[key]) != str(last_data.get(key)):
            changes[key] = {
                "old": last_data.get(key),
                "new": current_data[key]
            }


    with open(STATUS_FILE, "w") as f:
        json.dump(current_data, f, indent=2)

 
    def send_discord_alert(changes):
        content = f"📣 Instagram update for **{TARGET_USERNAME}**:\n\n"
        for key, val in changes.items():
            content += f"**{key.title()}**: {val['old']} → {val['new']}\n"

        payload = {"content": content}
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            if response.status_code == 204:
                log_message("✅ Discord alert sent.")
            else:
                log_message(f"⚠️ Failed to send Discord message: {response.text}")
        except Exception as e:
            log_message(f"❌ Error sending Discord alert: {e}")

    if changes:
        send_discord_alert(changes)
    else:
        log_message("ℹ️ No changes detected.")

    # --- Done ---
    driver.quit()
    log_message("🏁 Script finished successfully")

except Exception as e:
    error_text = traceback.format_exc()
    log_message("❌ Script crashed:\n" + error_text)
