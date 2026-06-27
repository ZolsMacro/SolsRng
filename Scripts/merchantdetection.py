import time
import os
import json
import requests
import keyboard
import pyautogui
import autoit
import pytesseract
import cv2
import numpy as np
import io
import pygetwindow as gw
from datetime import datetime
import ctypes

# DPI FIX
ctypes.windll.user32.SetProcessDPIAware()


class ZolMacro:
    def __init__(self):
        self._mt_running = False
        self.last_merchant_interaction = 0

        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tesseract_dir = os.path.join(self.root_dir, "Tesseract-OCR")

        pytesseract.pytesseract.tesseract_cmd = os.path.join(tesseract_dir, "tesseract.exe")
        os.environ["TESSDATA_PREFIX"] = os.path.join(tesseract_dir, "tessdata")

        self.config_path = os.path.join(self.root_dir, "config.txt")
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                self.config = json.load(f)

            self.cal = self.config.get("Calibrations", {})
            self.merchant_cfg = self.config.get("Merchant", {})
            self.user_id = self.config.get("UserId")
            self.webhook_urls = self.config.get("WebHooks", {}).get("webhook_urls", [])
        else:
            exit(1)

    def get_roblox_window(self):
        windows = gw.getWindowsWithTitle("Roblox")
        if not windows:
            return None

        w = windows[0]
        hwnd = w._hWnd

        from ctypes import wintypes
        rect = wintypes.RECT()
        ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))

        point = wintypes.POINT(0, 0)
        ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(point))

        return {
            "left": point.x,
            "top": point.y,
            "width": rect.right,
            "height": rect.bottom
        }

    # ✅ NO scaling anymore — raw config coords only
    def pos(self, key):
        win = self.get_roblox_window()
        if not win:
            return (0, 0)

        c = self.cal.get(key, {})
        return (
            int(win["left"] + c.get("x", 0)),
            int(win["top"] + c.get("y", 0))
        )

    def safe_click(self, pos):
        x, y = pos
        autoit.mouse_move(x, y, speed=2)
        time.sleep(0.05)
        autoit.mouse_down("left")
        time.sleep(0.05)
        autoit.mouse_up("left")

    def spam_e_fast(self):
        end = time.time() + 0.6
        while time.time() < end:
            keyboard.press_and_release("e")
            time.sleep(0.05)

    def skip_dialogue(self, times=6):
        for _ in range(times):
            self.safe_click(self.pos("dialogue_skip"))
            time.sleep(0.05)

    def detect_merchant_name(self):
        try:
            windows = gw.getWindowsWithTitle("Roblox")
            if not windows:
                return None

            rbx = windows[0]
            screenshot = pyautogui.screenshot(
                region=(rbx.left, rbx.top, rbx.width, rbx.height)
            )

            img = np.array(screenshot)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, None, fx=1.5, fy=1.5)
            gray = cv2.bilateralFilter(gray, 9, 75, 75)
            _, thresh = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)

            text = pytesseract.image_to_string(thresh, config="--psm 6").lower()

            if "mari" in text:
                return "Mari"
            if "jester" in text:
                return "Jester"
            if "rin" in text:
                return "Rin"

            return None

        except:
            return None

    def should_ping(self, merchant):
        m = self.merchant_cfg
        if merchant == "Mari" and m.get("MariPing"):
            return f"<@{self.user_id}>"
        if merchant == "Jester" and m.get("JesterPing"):
            return f"<@{self.user_id}>"
        if merchant == "Rin" and m.get("RinPing"):
            return f"<@{self.user_id}>"
        return ""

    def wait_for_shop_ui(self, timeout=8):
        start = time.time()
        while time.time() - start < timeout:
            try:
                windows = gw.getWindowsWithTitle("Roblox")
                if windows:
                    rbx = windows[0]
                    screenshot = pyautogui.screenshot(
                        region=(rbx.left, rbx.top, rbx.width, rbx.height)
                    )

                    img = np.array(screenshot)
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

                    text = pytesseract.image_to_string(thresh).lower()
                    if "shop" in text:
                        return True
            except:
                pass

            time.sleep(0.05)

        return False

    def send_webhook(self, npc_name):
        try:
            colors = {"Mari": 16777215, "Jester": 10181046, "Rin": 15105570}

            windows = gw.getWindowsWithTitle("Roblox")
            if not windows:
                return

            rbx = windows[0]
            img_buffer = io.BytesIO()

            screenshot = pyautogui.screenshot(
                region=(rbx.left, rbx.top, rbx.width, rbx.height)
            )
            screenshot.save(img_buffer, format="PNG")
            img_buffer.seek(0)

            payload = {
                "content": self.should_ping(npc_name),
                "embeds": [{
                    "title": "Merchant Detected",
                    "description": f"Merchant detected: **{npc_name}**",
                    "color": colors.get(npc_name, 16777215),
                    "image": {"url": "attachment://stock.png"},
                    "footer": {"text": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                }]
            }

            for url in self.webhook_urls:
                img_buffer.seek(0)
                requests.post(
                    url,
                    data={"payload_json": json.dumps(payload)},
                    files={"file": ("stock.png", img_buffer)},
                    timeout=15
                )

        except:
            pass

    def Merchant_Handler(self):
        try:
            self.spam_e_fast()

            merchant = None
            for _ in range(10):
                merchant = self.detect_merchant_name()
                if merchant:
                    break
                time.sleep(0.05)

            if not merchant:
                return

            self.last_merchant_interaction = time.time()

            self.skip_dialogue(6)
            self.safe_click(self.pos("open_merchant"))
            self.skip_dialogue(4)

            if self.wait_for_shop_ui(timeout=10):
                self.safe_click(self.pos("close_merchant_shop"))
                self.send_webhook(merchant)

                keyboard.press_and_release("esc")
                time.sleep(0.05)
                keyboard.press_and_release("r")
                time.sleep(0.05)
                keyboard.press_and_release("enter")
                time.sleep(4.0)

        except:
            pass

    def _merchant_teleporter_impl(self):
        if self._mt_running:
            return

        self._mt_running = True

        try:
            print("Merchant Detection starting...")

            self.safe_click(self.pos("open_inventory"))
            self.safe_click(self.pos("inventory_items_tab"))
            self.safe_click(self.pos("inventory_search_bar"))

            autoit.send("teleport")
            time.sleep(0.05)

            self.safe_click(self.pos("first_inventory_slot"))
            self.safe_click(self.pos("inventory_use"))
            self.safe_click(self.pos("inventory_close"))

            time.sleep(2.0)

            self.Merchant_Handler()

        except Exception as e:
            print(f"Merchant Impl Error: {e}")

        finally:
            self._mt_running = False


if __name__ == "__main__":
    macro = ZolMacro()

    while True:
        macro._merchant_teleporter_impl()
        time.sleep(1.0)