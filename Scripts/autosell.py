import time
import autoit
import sys
import os
import pytesseract
import mss
import numpy as np
from PIL import Image, ImageOps

current_dir = os.path.dirname(os.path.abspath(__file__))
script_dir = os.path.dirname(current_dir) 
tesseract_exe_path = os.path.join(script_dir, "Tesseract-OCR", "tesseract.exe")
tessdata_path = os.path.join(script_dir, "Tesseract-OCR", "tessdata")

pytesseract.pytesseract.tesseract_cmd = tesseract_exe_path
os.environ["TESSDATA_PREFIX"] = tessdata_path

FIRST_SLOT_REGION = (766, 344, 891, 469)

SELL_CONFIG = {
    "fishing_flarg_dialogue_box":       [1046, 782],
    "fishing_shop_sell_button":         [957,  934],
    "fishing_shop_close_button":        [1458, 269],
    "fishing_shop_first_fish":          [827,  404],
    "fishing_shop_sell_all_button":     [662,  799],
    "fishing_confirm_sell_all_button":  [800,  619],
    "collections_button":               [41,   457],
    "exit_collections_button":          [380,  128],
    "action_delay_ms": 100,
}

WALK_TO_SELL_EVENTS = [
    {"t": 0.4576, "type": "key_down", "key": "a"}, {"t": 0.471262, "type": "key_down", "key": "w"}, 
    {"t": 6.194382, "type": "key_up", "key": "w"}, {"t": 6.199392, "type": "key_up", "key": "a"}, 
    {"t": 6.752266, "type": "key_down", "key": "d"}, {"t": 6.980446, "type": "key_up", "key": "d"}, 
    {"t": 7.259337, "type": "key_down", "key": "w"}, {"t": 7.59426, "type": "key_up", "key": "w"}, 
    {"t": 7.630302, "type": "key_down", "key": "a"}, {"t": 7.98328, "type": "key_down", "key": "w"}, 
    {"t": 10.613272, "type": "key_up", "key": "w"}, {"t": 10.656335, "type": "key_up", "key": "a"}, 
    {"t": 10.750228, "type": "key_down", "key": "d"}, {"t": 11.104218, "type": "key_down", "key": "a"}, 
    {"t": 11.105522, "type": "key_up", "key": "d"}, {"t": 11.143553, "type": "key_down", "key": "space"}, 
    {"t": 11.270252, "type": "key_up", "key": "space"}, {"t": 12.055254, "type": "key_down", "key": "space"}, 
    {"t": 12.198157, "type": "key_up", "key": "space"}, {"t": 12.474242, "type": "key_down", "key": "w"}, 
    {"t": 12.537233, "type": "key_up", "key": "a"}, {"t": 13.562389, "type": "key_up", "key": "w"}, 
    {"t": 13.72922, "type": "key_down", "key": "space"}, {"t": 13.809357, "type": "key_down", "key": "d"}, 
    {"t": 13.874365, "type": "key_up", "key": "space"}, {"t": 14.733302, "type": "key_down", "key": "w"}, 
    {"t": 14.746239, "type": "key_up", "key": "d"}, {"t": 15.026838, "type": "key_up", "key": "w"}
]

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def to_autoit_key(key):
    key = key.lower().strip()
    if key == "space": return "SPACE"
    return key.upper()

def tap_key(key):
    token = to_autoit_key(key)
    if len(token) == 1:
        autoit.send(token.lower())
    else:
        autoit.send(f"{{{token}}}")

def is_first_slot_occupied():
    try:
        time.sleep(0.3)
        
        left, top, right, bottom = FIRST_SLOT_REGION
        width = right - left
        height = bottom - top
        
        with mss.mss() as sct:
            shot = sct.grab({"left": left, "top": top, "width": width, "height": height})
            if shot is None:
                return False
                
            screenshot = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        
        screenshot.save("debug_slot.png") 
        
        screenshot = ImageOps.grayscale(screenshot)
        screenshot = ImageOps.autocontrast(screenshot)
        
        text = pytesseract.image_to_string(screenshot, config='--psm 7').strip()
        cleaned_text = "".join([c for c in text if c.isalnum()])
        
        if len(cleaned_text) >= 1:
            log(f"Fish Detected: {cleaned_text}")
            return True
        return False
    except Exception as e:
        log(f"OCR Error: {e}")
        return False

def run_respawn():
    log("Respawning...")
    tap_key("esc")
    time.sleep(0.25)
    tap_key("r")
    time.sleep(0.25)
    tap_key("enter")
    time.sleep(0.25) 

def run_walking_path():
    log("Walking to merchant...")
    last_t = 0.0
    for ev in WALK_TO_SELL_EVENTS:
        t = ev["t"]
        dt = t - last_t
        if dt > 0:
            time.sleep(dt)
        key_token = to_autoit_key(ev["key"])
        if ev["type"] == "key_down":
            autoit.send(f"{{{key_token} down}}")
        else:
            autoit.send(f"{{{key_token} up}}")
        last_t = t
    time.sleep(0.25)
    tap_key("e")
    time.sleep(0.5)

def run_sell_logic():
    log("Navigating shop menus...")
    delay = SELL_CONFIG["action_delay_ms"] / 1000.0
    
    autoit.mouse_click("left", *SELL_CONFIG["fishing_flarg_dialogue_box"], speed=3)
    time.sleep(0.5 + delay)
    
    autoit.mouse_click("left", *SELL_CONFIG["fishing_shop_sell_button"], speed=3)
    time.sleep(1.0 + delay)
    
    while True:
        if not is_first_slot_occupied():
            break
            
        autoit.mouse_click("left", *SELL_CONFIG["fishing_shop_first_fish"], speed=3)
        time.sleep(0.25 + delay)
        autoit.mouse_click("left", *SELL_CONFIG["fishing_shop_sell_all_button"], speed=3)
        time.sleep(0.25 + delay)
        autoit.mouse_click("left", *SELL_CONFIG["fishing_confirm_sell_all_button"], speed=3)
        time.sleep(0.5 + delay)
        
    log("Inventory empty. Closing.")
    autoit.mouse_click("left", *SELL_CONFIG["fishing_shop_close_button"], speed=3)
    time.sleep(0.25)

def main():
    log("Script starting. Tab in now!")
    try:
        autoit.mouse_click("left", *SELL_CONFIG["collections_button"], speed=3)
        time.sleep(0.25)
        autoit.mouse_click("left", *SELL_CONFIG["exit_collections_button"], speed=3)
        time.sleep(0.25)
        run_respawn()
        run_walking_path()
        run_sell_logic()
        run_respawn()
        log("Done.")
    except KeyboardInterrupt:
        log("Stopped.")

if __name__ == "__main__":
    main()