import subprocess

adb = r"C:\Users\NManh\AppData\Local\Android\Sdk\platform-tools\adb.exe"
dev = "100.71.117.39:5555"

# test_wake_and_capture.py:
# run_adb("shell", "dumpsys power | grep mWakefulness=")
cmd1 = [adb, "-s", dev, "shell", "dumpsys power | grep mWakefulness="]
r1 = subprocess.run(cmd1, capture_output=True, text=True)
print("cmd1 (test_wake_and_capture):", r1.stdout.strip())

# android_checkin.py:
# self._run_adb_raw("shell", "dumpsys", "power")
cmd2 = [adb, "-s", dev, "shell", "dumpsys", "power"]
r2 = subprocess.run(cmd2, capture_output=True, text=True)
print("cmd2 lines count:", len(r2.stdout.splitlines()))

# dumpsys window in android_checkin.py:
# self._run_adb_raw("shell", "dumpsys window | grep -E 'isKeyguardShowing|showing='")
cmd3 = [adb, "-s", dev, "shell", "dumpsys window | grep -E 'isKeyguardShowing|showing='"]
r3 = subprocess.run(cmd3, capture_output=True, text=True)
print("cmd3 (android_checkin):", r3.stdout.strip())
