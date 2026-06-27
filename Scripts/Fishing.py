import sys
import time
import autoit
import cv2
import numpy as np
import pyautogui
import mmap
try:
    import mss
except Exception:
    mss = None

CONFIG = {
    "fishing_bar_region": [750, 753, 416, 38],
    "fishing_detect_pixel": [1175, 836],
    "fishing_click_position": [846, 835],
    "fishing_midbar_sample_pos": [955, 767],
    "fishing_close_button_pos": [1113, 342],
    "collections_button": [41, 457],
    "exit_collections_button": [380, 128],
    "reel_sleep": 0.004,
    "tolerance": 12,
    "click_burst": 2
}

WALK_TO_FISH_EVENTS = [
    {"type":"key_down","key":"w","t":0.739},
    {"type":"key_down","key":"a","t":0.741},
    {"type":"key_up","key":"a","t":1.438},
    {"type":"key_up","key":"w","t":8.1}
]

def signal_catch():
    try:
        shm = mmap.mmap(-1, 1, tagname="fish_sync")
        shm[0] = 1 
        shm.close()
    except Exception:
        pass

def tap_key(key):
    k = key.upper()
    if k == "SPACE": autoit.send("{SPACE}")
    elif k == "ESC": autoit.send("{ESC}")
    elif k == "ENTER": autoit.send("{ENTER}")
    else: autoit.send(k.lower())

def run_setup_sequence():
    autoit.mouse_click("left", *CONFIG["collections_button"], speed=3)
    time.sleep(0.25)
    autoit.mouse_click("left", *CONFIG["exit_collections_button"], speed=3)
    time.sleep(0.25)
    tap_key("ESC")
    time.sleep(0.25)
    tap_key("R")
    time.sleep(0.25)
    tap_key("ENTER")
    time.sleep(0.25)

def run_walking_to_water():
    last_t = 0.0
    for ev in WALK_TO_FISH_EVENTS:
        t = ev["t"]
        dt = t - last_t
        if dt > 0: time.sleep(dt)
        token = ev["key"].upper()
        if ev["type"] == "key_down":
            autoit.send(f"{{{token} down}}")
        else:
            autoit.send(f"{{{token} up}}")
        last_t = t
    time.sleep(0.25)

def get_pixel(x, y, sct):
    if sct:
        shot = sct.grab({"left": x, "top": y, "width": 1, "height": 1})
        arr = np.frombuffer(shot.bgra, dtype=np.uint8).reshape((1, 1, 4))
        return int(arr[0,0,2]), int(arr[0,0,1]), int(arr[0,0,0])
    p = pyautogui.pixel(x, y)
    return p[0], p[1], p[2]

def check_color(bar_color, sct):
    x, y, w, h = CONFIG["fishing_bar_region"]

    scan_h = 5 
    scan_y = y + ((h - scan_h) // 2)
    
    if sct:
        shot = sct.grab({"left": x, "top": scan_y, "width": w, "height": scan_h})
        bgr = np.frombuffer(shot.bgra, dtype=np.uint8).reshape((scan_h, w, 4))[:,:,:3]
    else:
        img = pyautogui.screenshot(region=(x, scan_y, w, scan_h))
        bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    low = np.array([max(0, bar_color[2]-CONFIG["tolerance"]), max(0, bar_color[1]-CONFIG["tolerance"]), max(0, bar_color[0]-CONFIG["tolerance"])])
    upp = np.array([min(255, bar_color[2]+CONFIG["tolerance"]), min(255, bar_color[1]+CONFIG["tolerance"]), min(255, bar_color[0]+CONFIG["tolerance"])])
    return np.any(cv2.inRange(bgr, low, upp))

def safe_click(pos):
    x, y = pos
    autoit.mouse_move(x, y, speed=2)
    time.sleep(0.05)
    autoit.mouse_down("left")
    time.sleep(0.05)
    autoit.mouse_up("left")

def fast_click(pos):
    x, y = pos
    autoit.mouse_click("left", x, y, speed=0)

def main():
    sct = mss.mss() if mss else None

    run_setup_sequence()
    run_walking_to_water()

    safe_click(CONFIG["fishing_click_position"])
    time.sleep(0.25)

    r, g, b = get_pixel(CONFIG["fishing_detect_pixel"][0], CONFIG["fishing_detect_pixel"][1], sct)
    if r > 250 and g > 250 and b > 250:
        safe_click(CONFIG["fishing_click_position"])
        time.sleep(0.25)

    while True:
        r, g, b = get_pixel(CONFIG["fishing_detect_pixel"][0], CONFIG["fishing_detect_pixel"][1], sct)

        if r > 250 and g > 250 and b > 250:

            fast_click(CONFIG["fishing_click_position"])
            time.sleep(0.18)

            r2, g2, b2 = get_pixel(CONFIG["fishing_detect_pixel"][0], CONFIG["fishing_detect_pixel"][1], sct)
            if r2 > 250 and g2 > 250 and b2 > 250:
                fast_click(CONFIG["fishing_click_position"])
                time.sleep(0.18)

            bar_color = get_pixel(CONFIG["fishing_midbar_sample_pos"][0], CONFIG["fishing_midbar_sample_pos"][1], sct)

            start_reel = time.time()
            while time.time() - start_reel < 9:
                found = check_color(bar_color, sct)
                
                if not found:
                    for _ in range(CONFIG["click_burst"]):
                        fast_click(CONFIG["fishing_click_position"])
                
                time.sleep(CONFIG["reel_sleep"])

            time.sleep(0.25)

            for _ in range(3):
                safe_click(CONFIG["fishing_close_button_pos"])
                time.sleep(0.25)

            signal_catch()
            time.sleep(0.42)

            safe_click(CONFIG["fishing_click_position"])
            time.sleep(0.25)

if __name__ == "__main__":
    main()