import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import edge_rewards_bot
from selenium.webdriver.common.by import By

config = edge_rewards_bot.load_config()
config['browser_settings']['headless'] = True
driver = edge_rewards_bot.create_edge_driver(is_mobile=False, config=config, profile_target={'id': '3', 'path': './edge_profile_3', 'profile_directory': 'Profile 2'})

try:
    driver.get('https://rewards.bing.com/earn')
    time.sleep(3)
    btns = driver.find_elements(By.XPATH, '//*[contains(text(), "Points breakdown")]')
    if btns:
        driver.execute_script("arguments[0].click();", btns[0])
        time.sleep(2)
        dialogs = driver.find_elements(By.CSS_SELECTOR, '[role="dialog"], [class*="modal"]')
        for d in dialogs:
            print("DIALOG TEXT:\n", d.text)
    else:
        print("Button not found")
except Exception as e:
    print("Error:", e)
finally:
    driver.quit()
