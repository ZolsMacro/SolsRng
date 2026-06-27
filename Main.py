import os
import json
import subprocess
import webview
import sys
import threading
import time
import mmap
import keyboard

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

overlay_window = None
main_window = None
biome_process = None
aura_process = None
fishing_process = None
merchant_process = None
manual_stop = False
macro_active = False

fishing_enabled = False
biome_enabled = False
aura_enabled = False
merchant_enabled = False


class API:

    def start_macro(self):
        global macro_active, fishing_enabled, biome_enabled, aura_enabled, merchant_enabled
        if macro_active:
            return True
        
        macro_active = True
        self.sync_ui_status()

        if biome_enabled:
            self.run_biome_detection()

        if aura_enabled:
            self.run_aura_detection()

        if fishing_enabled:
            self.run_fishing_bot()

        if merchant_enabled:
            self.run_merchant_detection()

        return True

    def stop_macro(self):
        global macro_active    
        if not macro_active:
            return True

        macro_active = False
        self.sync_ui_status()
        
        self.stop_fishing_bot()
        self.stop_biome_detection()
        self.stop_aura_detection()
        self.stop_merchant_detection()

        try:
            for key in ['w', 'a', 's', 'd', 'space']:
                if keyboard.is_pressed(key):
                    keyboard.release(key)
        except:
            pass

        return True

    def sync_ui_status(self):
        global main_window, macro_active
        if main_window:
            def dispatch():
                try:
                    main_window.evaluate_js(f"window.updateMasterStatus({json.dumps(macro_active)})")
                except:
                    pass
            threading.Thread(target=dispatch, daemon=True).start()

    def load_config_file(self):
        path = os.path.join(BASE_DIR, "config.txt")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}

    def save_config_file(self, data):
        path = os.path.join(BASE_DIR, "config.txt")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def set_user_id(self, user_id):
        data = self.load_config_file()
        data["UserId"] = str(user_id)
        self.save_config_file(data)
        return True

    def set_webhook(self, webhook_url):
        data = self.load_config_file()
        if "WebHooks" not in data:
            data["WebHooks"] = {}
        data["WebHooks"]["webhook_urls"] = [str(webhook_url)]
        self.save_config_file(data)
        return True

    def set_private_server(self, server_link):
        data = self.load_config_file()
        data["Private Server"] = str(server_link)
        self.save_config_file(data)
        return True

    def set_biome_module_state(self, is_enabled):
        global biome_enabled, macro_active
        biome_enabled = bool(is_enabled)

        if macro_active:
            if biome_enabled:
                self.run_biome_detection()
            else:
                self.stop_biome_detection()
        return True

    def run_biome_detection(self):
        global biome_process, macro_active
        if not macro_active:
            macro_active = True
            self.sync_ui_status()

        script = os.path.join(BASE_DIR, "Scripts", "biomedetection.py")
        if biome_process and biome_process.poll() is None:
            return True

        biome_process = subprocess.Popen([sys.executable, script])
        return True

    def stop_biome_detection(self):
        global biome_process
        if biome_process and biome_process.poll() is None:
            try:
                biome_process.terminate()
                biome_process.wait(timeout=2)
            except:
                pass
        biome_process = None
        return True

    def set_aura_module_state(self, is_enabled):
        global aura_enabled, macro_active
        aura_enabled = bool(is_enabled)

        if macro_active:
            if aura_enabled:
                self.run_aura_detection()
            else:
                self.stop_aura_detection()
        return True

    def run_aura_detection(self):
        global aura_process, macro_active
        if not macro_active:
            macro_active = True
            self.sync_ui_status()

        script = os.path.join(BASE_DIR, "Scripts", "auradetection.py")
        if aura_process and aura_process.poll() is None:
            return True

        aura_process = subprocess.Popen([sys.executable, script])
        return True

    def stop_aura_detection(self):
        global aura_process
        if aura_process and aura_process.poll() is None:
            try:
                aura_process.terminate()
                aura_process.wait(timeout=2)
            except:
                pass
        aura_process = None
        return True

    def set_merchant_module_state(self, is_enabled):
        global merchant_enabled, macro_active
        merchant_enabled = bool(is_enabled)

        if macro_active:
            if merchant_enabled:
                self.run_merchant_detection()
            else:
                self.stop_merchant_detection()
        return True

    def run_merchant_detection(self):
        global merchant_process, macro_active
        if not macro_active:
            macro_active = True
            self.sync_ui_status()

        script = os.path.join(BASE_DIR, "Scripts", "merchantdetection.py")
        if merchant_process and merchant_process.poll() is None:
            return True

        merchant_process = subprocess.Popen([sys.executable, script])
        return True

    def stop_merchant_detection(self):
        global merchant_process
        if merchant_process and merchant_process.poll() is None:
            try:
                merchant_process.terminate()
                merchant_process.wait(timeout=2)
            except:
                pass
        merchant_process = None
        return True

    def get_merchant_config(self):
        data = self.load_config_file()
        if "Merchant" not in data:
            data["Merchant"] = {}
        return data["Merchant"]

    def set_merchant_flag(self, key, value):
        data = self.load_config_file()
        if "Merchant" not in data:
            data["Merchant"] = {}
        data["Merchant"][key] = value
        self.save_config_file(data)
        return True

    def set_fishing_module_state(self, is_enabled):
        global fishing_enabled, macro_active
        fishing_enabled = bool(is_enabled)

        if macro_active:
            if fishing_enabled:
                self.run_fishing_bot()
            else:
                self.stop_fishing_bot()
        return True

    def run_fishing_bot(self):
        global fishing_process, manual_stop, macro_active
        if not macro_active:
            macro_active = True
            self.sync_ui_status()

        if fishing_process and fishing_process.poll() is None:
            return True

        manual_stop = False

        def bot_loop():
            global fishing_process, manual_stop, macro_active
            while not manual_stop and macro_active:
                try:
                    shm = mmap.mmap(-1, 1, tagname="fish_sync")
                    shm[0] = 0
                except:
                    shm = mmap.mmap(-1, 1, tagname="fish_sync")
                    shm[0] = 0

                fish_script = os.path.join(BASE_DIR, "Scripts", "fishing.py")
                fishing_process = subprocess.Popen([sys.executable, fish_script])

                collected_fish = 0
                threshold_reached = False

                while fishing_process and fishing_process.poll() is None:
                    if manual_stop or not macro_active:
                        try:
                            fishing_process.terminate()
                        except:
                            pass
                        break

                    if shm[0] == 1:
                        collected_fish += 1
                        shm[0] = 0

                        config = self.load_config_file()
                        threshold = int(config.get("Fishing", {}).get("SellThreshold", 20))

                        if collected_fish >= threshold:
                            threshold_reached = True
                            try:
                                fishing_process.terminate()
                                fishing_process.wait()
                            except:
                                pass
                            break

                    time.sleep(0.1)

                shm.close()

                if manual_stop or not macro_active:
                    break

                if threshold_reached and macro_active:
                    sell_script = os.path.join(BASE_DIR, "Scripts", "autosell.py")
                    sell_process = subprocess.Popen([sys.executable, sell_script])

                    while sell_process.poll() is None:
                        if manual_stop or not macro_active:
                            try:
                                sell_process.terminate()
                            except:
                                pass
                            break
                        time.sleep(0.5)
                
                time.sleep(0.5)

        threading.Thread(target=bot_loop, daemon=True).start()
        return True

    def stop_fishing_bot(self):
        global fishing_process, manual_stop
        manual_stop = True

        if fishing_process:
            try:
                fishing_process.terminate()
                fishing_process.wait(timeout=2)
            except:
                pass
        fishing_process = None
        return True

    def get_fishing_config(self):
        data = self.load_config_file()
        return data.get("Fishing", {"SellThreshold": 20})

    def set_fishing_config(self, key, value):
        data = self.load_config_file()
        if "Fishing" not in data:
            data["Fishing"] = {}
        data["Fishing"][key] = value
        self.save_config_file(data)
        return True

    def get_calibrations(self):
        data = self.load_config_file()
        return data.get("Calibrations", {})

    def set_calibration(self, key, value):
        data = self.load_config_file()
        if "Calibrations" not in data:
            data["Calibrations"] = {}

        if not key or not isinstance(key, str) or key.lower() in ["null", "none", "default", "undefined"]:
            return False
        if not isinstance(value, dict):
            return False

        x = value.get("x")
        y = value.get("y")
        if x is None or y is None:
            return False

        data["Calibrations"][key] = {"x": int(x), "y": int(y)}
        self.save_config_file(data)
        return True

    def emit_calibration_result(self, data):
        try:
            config = self.load_config_file()
            if "Calibrations" not in config:
                config["Calibrations"] = {}

            key = data.get("key")
            x = data.get("x")
            y = data.get("y")

            config["Calibrations"][key] = {"x": x, "y": y}
            self.save_config_file(config)

            if main_window:
                main_window.evaluate_js(f"window.setCalibrationValue({x}, {y})")
            return True
        except:
            return False

    def open_overlay(self):
        global overlay_window, main_window
        overlay_window = webview.create_window(
            "overlay",
            os.path.join(BASE_DIR, "Gui/Events/calibrationselect.html"),
            js_api=self,
            fullscreen=True,
            frameless=True,
            transparent=True
        )
        main_window.hide()

    def close_overlay(self):
        global overlay_window, main_window
        if overlay_window:
            overlay_window.destroy()
            overlay_window = None
        main_window.show()


api = API()


def keyboard_handler(event):
    if event.event_type == keyboard.KEY_DOWN:
        if event.name == 'f1':
            api.start_macro()
        elif event.name == 'f2':
            api.stop_macro()


def register_hotkeys():
    keyboard.hook(keyboard_handler)
    keyboard.wait()


if __name__ == "__main__":
    main_window = webview.create_window(
        "Zol Macro",
        os.path.join(BASE_DIR, "Index.html"),
        js_api=api,
        width=1000,
        height=700
    )
    
    threading.Thread(target=register_hotkeys, daemon=True).start()
    webview.start(gui="qt", http_server=True)