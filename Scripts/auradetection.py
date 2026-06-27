import re
import time
import os
import json
import requests
import threading
import colorsys
import glob
import io
import pyautogui
import pygetwindow as gw
from PIL import ImageGrab
from datetime import datetime

class DetectionMixin:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt")
        self.webhook_url = self.load_webhook_from_config()
        self.auras_url = "https://raw.githubusercontent.com/ZolsMacro/SolsRng/refs/heads/Assets/Auras.json"
        self.log_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Roblox', 'logs')
        
        self.last_aura_found = None
        self.aura_log_pos = 0 
        self.last_file_checked = None 
        self.detection_running = True
        self.current_biome = "NORMAL"
        self.auras_data = self.load_auras_json()

        self.aura_styles = {
            "BasicAuras": ("⚪ Basic", 0xFFFFFF),
            "EpicAuras": ("🟣 Epic", 0xBF00FF),
            "UniqueAuras": ("🟠 Unique", 0xFFA500),
            "LegendaryAuras": ("🟡 Legendary", 0xFFFF00),
            "MythicAuras": ("🌸 Mythic", 0xFF69B4),
            "ExaltedAuras": ("🔵 Exalted", 0x0000FF),
            "GloriousAuras": ("🔥 Glorious", 0xFF0033),
            "TranscendentAuras": ("🌌 Transcendent", 0x3498db),
            "SpecialAuras": ("⭐ Special", 0xFF4500)
        }

    def load_webhook_from_config(self):
        default_webhook = "https://discord.com/api/webhooks/1491299022655455333/cO9266gD311Ve58-rnfggBZeTfr6oWBo1k9ufAybWhbp5noqaWGorzT59Bj7eFlo9BqK"
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    urls = data.get("WebHooks", {}).get("webhook_urls", [])
                    if urls and urls[0].strip():
                        return urls[0].strip()
        except:
            pass
        return default_webhook

    def extract_json(self, line):
        start = line.find('{')
        if start == -1: return None
        depth = 0
        for i in range(start, len(line)):
            if line[i] == '{': depth += 1
            elif line[i] == '}':
                depth -= 1
                if depth == 0: return line[start:i + 1]
        return None

    def dual_color_loop(self, webhook_url, message_id, payload, color1, color2):
        current_is_first = True
        for _ in range(300):
            if not self.detection_running: break
            chosen_color = int(color1) if current_is_first else int(color2)
            payload["embeds"][0]["color"] = chosen_color
            try:
                requests.patch(f"{webhook_url}/messages/{message_id}", json=payload, timeout=5)
            except:
                break
            current_is_first = not current_is_first
            time.sleep(0.5)

    def rainbow_loop(self, webhook_url, message_id, payload):
        hue = 0
        for _ in range(150):
            if not self.detection_running: break
            rgb = colorsys.hsv_to_rgb(hue, 1, 1)
            color_int = (int(rgb[0]*255) << 16) + (int(rgb[1]*255) << 8) + int(rgb[2]*255)
            payload["embeds"][0]["color"] = color_int
            try:
                requests.patch(f"{webhook_url}/messages/{message_id}", json=payload, timeout=5)
            except:
                break
            hue += 0.05
            if hue > 1: hue = 0
            time.sleep(1.5)

    def handle_aura_detection(self, name):
        if not self.auras_data:
            self.auras_data = self.load_auras_json()

        target_info = None
        target_category = None
        search_name = name.lower().strip()

        for cat_key, cat_data in self.auras_data.items():
            for real_name, info in cat_data.items():
                if real_name.lower() == search_name:
                    target_info = info
                    name = real_name
                    target_category = cat_key
                    break
            if target_info: break

        if target_info:
            rarity = target_info.get("rarity", 1)
            raw_color = target_info.get("color")
            is_rgb = (str(raw_color).upper() == "RGB")
            is_dual = isinstance(raw_color, list) and len(raw_color) == 2
            
            label, default_col = self.aura_styles.get(target_category, ("❓ Unknown", 0x999999))
            
            if is_dual:
                start_color = int(raw_color[0])
            elif isinstance(raw_color, int):
                start_color = raw_color
            else:
                start_color = default_col if default_col else 0x3498db

            if start_color > 16777215: start_color = 16777215

            img_byte_arr = io.BytesIO()
            try:
                windows = [w for w in gw.getWindowsWithTitle('Roblox') if w.visible]
                if windows:
                    rbx = windows[0]
                    bbox = (rbx.left, rbx.top, rbx.right, rbx.bottom)
                    screenshot = ImageGrab.grab(bbox, all_screens=True)
                else:
                    screenshot = pyautogui.screenshot()
            except:
                screenshot = pyautogui.screenshot()
            
            screenshot.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            self.webhook_url = self.load_webhook_from_config()
            self.send_webhook(name, int(rarity), label, start_color, is_rgb, is_dual, raw_color, img_byte_arr)

    def send_webhook(self, name, rarity, category, color, is_rgb, is_dual, raw_color, img_byte_arr):
        current_time = datetime.now().strftime("%I:%M %p")
        payload = {
            "embeds": [{
                "title": f"✨ New Aura Detected!",
                "color": color,
                "fields": [
                    {"name": "Aura Name", "value": f"**{name}**", "inline": True},
                    {"name": "Rarity", "value": f"1/{rarity:,}", "inline": True},
                    {"name": "Biome", "value": f"🌍 {self.current_biome}", "inline": True}
                ],
                "image": {"url": "attachment://aura_shot.png"},
                "footer": {"text": f"Zols Macro • {current_time}"}
            }]
        }
        
        try:
            files = {"file": ("aura_shot.png", img_byte_arr, "image/png")}
            response = requests.post(
                f"{self.webhook_url}?wait=true", 
                data={"payload_json": json.dumps(payload)}, 
                files=files, 
                timeout=10
            )
            
            if response.status_code == 200:
                msg_id = response.json().get("id")
                if is_rgb:
                    threading.Thread(target=self.rainbow_loop, args=(self.webhook_url, msg_id, payload), daemon=True).start()
                elif is_dual:
                    threading.Thread(target=self.dual_color_loop, args=(self.webhook_url, msg_id, payload, raw_color[0], raw_color[1]), daemon=True).start()
        except:
            pass

    def load_auras_json(self):
        try:
            r = requests.get(self.auras_url, timeout=10)
            return json.loads(r.content.decode('utf-8-sig'))
        except: return {}

    def get_latest_log(self):
        files = glob.glob(os.path.join(self.log_path, "*_last.log"))
        return max(files, key=os.path.getmtime) if files else None

    def check_aura_in_logs(self, log_file_path):
        if log_file_path != self.last_file_checked:
            self.aura_log_pos = os.path.getsize(log_file_path) if self.last_file_checked is None else 0
            self.last_file_checked = log_file_path
        
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self.aura_log_pos)
                lines = f.readlines()
                self.aura_log_pos = f.tell()
            
            for line in lines:
                if "[BloxstrapRPC]" in line and "SetRichPresence" in line:
                    try:
                        json_str = self.extract_json(line)
                        if json_str:
                            log_data = json.loads(json_str)
                            new_biome = log_data.get("data", {}).get("largeImage", {}).get("hoverText")
                            if new_biome:
                                self.current_biome = new_biome.strip().upper()
                    except:
                        pass

                match = re.search(r'"state":"Equipped \\"(.*?)\\"', line)
                if match:
                    aura_name = match.group(1)
                    if aura_name != self.last_aura_found:
                        self.last_aura_found = aura_name
                        self.handle_aura_detection(aura_name)
        except:
            pass

if __name__ == "__main__":
    detector = DetectionMixin()
    while True:
        log = detector.get_latest_log()
        if log: detector.check_aura_in_logs(log)
        time.sleep(1)