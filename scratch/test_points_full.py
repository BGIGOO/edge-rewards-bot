import sys, os, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import edge_rewards_bot
from selenium.webdriver.common.by import By

config = edge_rewards_bot.load_config()
config['browser_settings']['headless'] = True
driver = edge_rewards_bot.create_edge_driver(is_mobile=False, config=config, profile_target={'id': '3', 'path': './edge_profile_3', 'profile_directory': 'Profile 2'})

try:
    driver.get('https://rewards.bing.com/earn')
    time.sleep(3)
    # Search for breakdown button
    btns = driver.find_elements(By.XPATH, '//*[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "breakdown") or contains(text(), "Chi tiết điểm") or contains(@aria-label, "breakdown") or contains(@href, "breakdown")]')
    print("Found btns:", len(btns))
    for b in btns:
        print(f"Tag: {b.tag_name}, Text: '{b.text}', aria: '{b.get_attribute('aria-label')}'")

    if btns:
        driver.execute_script("arguments[0].click();", btns[0])
        time.sleep(2)
        dialogs = driver.find_elements(By.CSS_SELECTOR, '[role="dialog"], [class*="modal"]')
        for d in dialogs:
            print("--- DIALOG CONTENT ---")
            print(d.text)
            print("----------------------")
finally:
    driver.quit()
