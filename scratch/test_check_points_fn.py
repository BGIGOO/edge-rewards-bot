import sys, os, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db
import edge_rewards_bot
from selenium.webdriver.common.by import By

def parse_rewards_breakdown_text(text):
    result = {
        "today_points": 0,
        "desktop_points": "0/90",
        "mobile_points": "0/60",
        "offers_points": 0,
        "total_points": 0
    }
    
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        # Today's points
        if re.search(r"today'?s?\s*points?|điểm\s*hôm\s*nay", line, re.I):
            m = re.search(r"(\d+)", line)
            if m and not line.lower().startswith("today"):
                result["today_points"] = int(m.group(1))
            elif i + 1 < len(lines) and re.match(r"^\d+$", lines[i+1]):
                result["today_points"] = int(lines[i+1])

        # Lifetime / Total points
        if re.search(r"^lifetime$|^tổng$|^tích lũy$", line, re.I):
            if i + 1 < len(lines):
                m = re.search(r"(\d[\d,]*)", lines[i+1])
                if m:
                    result["total_points"] = int(m.group(1).replace(",", ""))
        elif re.search(r"lifetime|tổng số điểm", line, re.I):
            m = re.search(r"(\d[\d,]*)", line)
            if m:
                result["total_points"] = int(m.group(1).replace(",", ""))

        # Desktop Bing search / Bing search
        if re.search(r"(desktop|pc)\s*(bing)?\s*search", line, re.I):
            if i + 1 < len(lines) and "/" in lines[i+1]:
                result["desktop_points"] = lines[i+1]
            else:
                m = re.search(r"(\d+\s*/\s*\d+)", line)
                if m:
                    result["desktop_points"] = m.group(1).replace(" ", "")
        elif re.search(r"^bing\s*search$", line, re.I):
            if i + 1 < len(lines) and "/" in lines[i+1]:
                result["desktop_points"] = lines[i+1]
            else:
                m = re.search(r"(\d+\s*/\s*\d+)", line)
                if m:
                    result["desktop_points"] = m.group(1).replace(" ", "")

        # Mobile Bing search
        if re.search(r"mobile\s*(bing)?\s*search", line, re.I):
            if i + 1 < len(lines) and "/" in lines[i+1]:
                result["mobile_points"] = lines[i+1]
            else:
                m = re.search(r"(\d+\s*/\s*\d+)", line)
                if m:
                    result["mobile_points"] = m.group(1).replace(" ", "")

        # Offers / Ưu đãi
        if re.search(r"^offers?$|^ưu đãi$", line, re.I):
            if i + 1 < len(lines) and re.match(r"^\d+$", lines[i+1]):
                result["offers_points"] = int(lines[i+1])
            else:
                m = re.search(r"(\d+)", line)
                if m:
                    result["offers_points"] = int(m.group(1))

    return result

p3 = db.get_profile_by_id(3)
print("Testing check points on Profile 3:", p3)

cfg = edge_rewards_bot.load_config()
cfg["browser_settings"]["headless"] = True

driver = None
try:
    driver = edge_rewards_bot.create_edge_driver(is_mobile=False, config=cfg, profile_target=p3)
    driver.get("https://rewards.bing.com/earn")
    time.sleep(3)
    
    # Check if redirect to login
    current_url = driver.current_url
    print("Current URL:", current_url)
    if "login.live.com" in current_url:
        print("Profile not logged in!")
    else:
        # Find breakdown button
        btns = driver.find_elements(
            By.XPATH,
            '//*[contains(translate(text(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "breakdown") or contains(text(), "Chi tiết điểm") or contains(@aria-label, "breakdown")]'
        )
        print("Found breakdown buttons:", len(btns))
        dialog_text = ""
        if btns:
            driver.execute_script("arguments[0].click();", btns[0])
            time.sleep(1.5)
            dialogs = driver.find_elements(By.CSS_SELECTOR, '[role="dialog"], [class*="modal"]')
            if dialogs:
                dialog_text = dialogs[0].text
        
        if not dialog_text:
            dialog_text = driver.find_element(By.TAG_NAME, "body").text
            
        points_data = parse_rewards_breakdown_text(dialog_text)
        print("Parsed points data:", points_data)
        
        # Update db
        updated = db.update_profile_db(
            p3["id"],
            total_points=points_data["total_points"],
            today_points=points_data["today_points"],
            desktop_points=points_data["desktop_points"],
            mobile_points=points_data["mobile_points"],
            offers_points=points_data["offers_points"],
            status="ready"
        )
        print("Updated in DB:", updated)
finally:
    if driver:
        driver.quit()
    p_dir = edge_rewards_bot.get_profile_abs_path(p3)
    edge_rewards_bot.kill_zombie_edge_processes(p_dir)
