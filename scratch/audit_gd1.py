import sys
import os
import sqlite3
import json

sys.stdout.reconfigure(encoding='utf-8')

print("=== CHECK DIRECTORIES ===")
print("src exists:", os.path.isdir("src"))
print("src/__init__.py exists:", os.path.exists("src/__init__.py"))
print("src/core exists:", os.path.isdir("src/core"))
print("src/core/__init__.py exists:", os.path.exists("src/core/__init__.py"))
print("src/core/paths.py exists:", os.path.exists("src/core/paths.py"))
print("data exists:", os.path.isdir("data"))
print("data/profiles exists:", os.path.isdir("data/profiles"))
print("data/screenshots exists:", os.path.isdir("data/screenshots"))

print("\n=== CHECK DATA FILES IN ROOT VS DATA ===")
print("data/rewards_bot.db exists:", os.path.exists("data/rewards_bot.db"))
print("data/keywords.txt exists:", os.path.exists("data/keywords.txt"))
print("root keywords.txt exists:", os.path.exists("keywords.txt"))
print("root rewards_bot.db exists:", os.path.exists("rewards_bot.db"))

print("\n=== CHECK SCREENSHOTS ===")
if os.path.isdir("data/screenshots"):
    print("data/screenshots contents:", os.listdir("data/screenshots"))
for p in ["test_device_screen.png", "web/android_checkin_before.png", "web/android_checkin_after.png"]:
    print(p, "exists in old place:", os.path.exists(p))

print("\n=== CHECK PROFILES IN data/profiles ===")
if os.path.isdir("data/profiles"):
    print("data/profiles:", os.listdir("data/profiles"))

print("\n=== CHECK DB PROFILES TABLE ===")
db_path = "data/rewards_bot.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print("Tables in DB:", [r[0] for r in cur.fetchall()])
    try:
        cur.execute("SELECT id, name, profile_path FROM profiles;")
        rows = cur.fetchall()
        for r in rows:
            print("  DB Profile:", r)
    except Exception as e:
        print("  Error reading profiles table:", e)
    conn.close()

print("\n=== CHECK CONFIG.JSON ===")
if os.path.exists("config.json"):
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)
    print("config.json profiles:")
    for p in cfg.get("profiles", []):
        print(" ", p.get("id"), p.get("name"), "->", p.get("profile_path"))
