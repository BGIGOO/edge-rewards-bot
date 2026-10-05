import json, time
from selenium.webdriver.common.by import By
from edge_rewards_bot import load_config, create_edge_driver

cfg = load_config()
p = cfg['profiles'][0]
cfg_copy = json.loads(json.dumps(cfg))
cfg_copy.setdefault('browser_settings', {})['headless'] = True

driver = create_edge_driver(is_mobile=False, config=cfg_copy, profile_target=p)
try:
    driver.get('https://rewards.bing.com/dashboard')
    time.sleep(3.5)

    breakdown_btns = driver.find_elements(
        By.XPATH,
        '//*[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "breakdown") or contains(text(), "Chi tiết điểm") or contains(@aria-label, "breakdown")]'
    )
    print('Found buttons:', len(breakdown_btns))
    if breakdown_btns:
        driver.execute_script('arguments[0].click();', breakdown_btns[0])
        time.sleep(2)
        dialogs = driver.find_elements(By.CSS_SELECTOR, '[role="dialog"], [class*="modal"]')
        print('Dialogs found:', len(dialogs))
        if dialogs:
            print('Dialog text:')
            print(dialogs[0].text)

finally:
    driver.quit()
