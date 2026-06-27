import os
import glob
import time
import json
import requests
from datetime import datetime, timezone

PING_BIOMES = {"CYBERSPACE", "DREAMSPACE", "GLITCHED"}

class BiomeDetector:
    def __init__(self):
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.txt"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.txt")
        ]
        
        self.config_path = possible_paths[0]
        for path in possible_paths:
            if os.path.exists(path):
                self.config_path = path
                break

        self.current_biome = "NORMAL"
        self.log_path = os.path.expandvars(r'%LOCALAPPDATA%\Roblox\logs')
        self.biome_data = {
            "NORMAL": {"color": 0xffffff, "thumbnail_url": "https://raw.githubusercontent.com/xVapure/Noteab-Macro/refs/heads/main/images/EGGLAND.png"},
            "WINDY": {"color": 0x9ae5ff, "thumbnail_url": "https://maxstellar.github.io/biome_thumb/WINDY.png"},
            "RAINY": {"color": 0x027cbd, "thumbnail_url": "https://maxstellar.github.io/biome_thumb/RAINY.png"},
            "SNOWY": {"color": 0xDceff9, "thumbnail_url": "https://maxstellar.github.io/biome_thumb/SNOWY.png"},
            "SAND STORM": {"color": 0x8F7057, "thumbnail_url": "https://maxstellar.github.io/biome_thumb/SAND%20STORM.png"},
            "HELL": {"color": 0xff4719, "thumbnail_url": "https://maxstellar.github.io/biome_thumb/HELL.png"},
            "STARFALL": {"color": 0x011ab7, "thumbnail_url": "https://maxstellar.github.io/biome_thumb/STARFALL.png"},
            "HEAVEN": {"color": 0xffe7a0, "thumbnail_url": "https://maxstellar.github.io/biome_thumb/HEAVEN.png"},
            "CORRUPTION": {"color": 0x6d32a8, "thumbnail_url": "https://maxstellar.github.io/biome_thumb/CORRUPTION.png"},
            "NULL": {"color": 0x838383, "thumbnail_url": "https://maxstellar.github.io/biome_thumb/NULL.png"},
            "GLITCHED": {"color": 0xbfff00, "thumbnail_url": "https://maxstellar.github.io/biome_thumb/GLITCHED.png"},
            "DREAMSPACE": {"color": 0xea9dda, "thumbnail_url": "https://maxstellar.github.io/biome_thumb/DREAMSPACE.png"},
            "CYBERSPACE": {"color": 0x0A1A3D, "thumbnail_url": "https://raw.githubusercontent.com/xVapure/Noteab-Macro/refs/heads/main/images/CYBERSPACE.png"},
            "EGGLAND": {"color": 0xFFD700, "thumbnail_url": "https://raw.githubusercontent.com/xVapure/Noteab-Macro/refs/heads/main/images/EGGLAND.png"},
            "THE HYPERSPACE REALM": {"color": 0x0d17d9, "thumbnail_url": "https://github.com/xVapure/Noteab-Macro/blob/main/images/biome_placeholder.png"}
        }

    def load_config_data(self):
        target_urls = []
        private_server = ""
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    urls = data.get("WebHooks", {}).get("webhook_urls", [])
                    if isinstance(urls, list):
                        for url in urls:
                            if url.strip() and url.strip() not in target_urls:
                                target_urls.append(url.strip())
                                
                    private_server = data.get("Private Server", "").strip()
        except:
            pass
            
        return target_urls, private_server

    def get_latest_log(self):
        files = glob.glob(os.path.join(self.log_path, "*_last.log"))
        return max(files, key=os.path.getmtime) if files else None

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

    def send_webhook(self, biome_name, status):
        webhook_urls, private_server = self.load_config_data()
        if not webhook_urls:
            return

        data = self.biome_data.get(biome_name, self.biome_data["NORMAL"])
        
        if status.lower() == "started":
            description = f"The biome is now **{biome_name}**"
        else:
            description = f"The biome **{biome_name}** has ended"
            
        if private_server:
            description += f"\n\n## **[Join Server]({private_server})**"

        embed = {
            "title": f"Biome {status.upper()}",
            "description": description,
            "color": data["color"],
            "thumbnail": {"url": data["thumbnail_url"]},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "footer": {"text": "Zol's Macro"}
        }
        payload = {"embeds": [embed]}
        if status.lower() == "started" and biome_name in PING_BIOMES:
            payload["content"] = "@everyone"
            
        for url in webhook_urls:
            try:
                requests.post(url, json=payload, timeout=5)
            except:
                pass

    def run(self):
        log_file = self.get_latest_log()
        if not log_file: return
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                if "[BloxstrapRPC]" in line and "SetRichPresence" in line:
                    try:
                        json_str = self.extract_json(line)
                        if not json_str: continue
                        log_data = json.loads(json_str)
                        raw_text = log_data.get("data", {}).get("largeImage", {}).get("hoverText")
                        if not raw_text: continue
                        
                        raw_text_upper = raw_text.strip().upper()
                        new_biome = None
                        
                        if raw_text_upper in self.biome_data:
                            new_biome = raw_text_upper
                        elif "HYPERSPACE" in raw_text_upper:
                            new_biome = "THE HYPERSPACE REALM"
                        else:
                            for key in self.biome_data.keys():
                                if key != "NORMAL" and key in raw_text_upper:
                                    new_biome = key
                                    break
                        
                        if not new_biome:
                            new_biome = raw_text_upper

                        if new_biome != self.current_biome:
                            old_biome = self.current_biome
                            if old_biome != "NORMAL":
                                self.send_webhook(old_biome, "Ended")
                            time.sleep(0.1)
                            self.current_biome = new_biome
                            self.send_webhook(self.current_biome, "Started")
                    except:
                        pass

if __name__ == "__main__":
    BiomeDetector().run()