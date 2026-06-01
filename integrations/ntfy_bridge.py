import os
import threading
import json
import requests
import time

class NtfyBridge:
    _instance = None

    def __init__(self):
        self.running = False
        self.thread = None
        self.topic = os.getenv("NTFY_TOPIC")
        self.server = os.getenv("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
        self.messages = []
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = NtfyBridge()
        return cls._instance

    def is_connected(self) -> bool:
        return self.running and bool(self.topic)

    def start(self):
        # Re-read env vars in case .env was loaded after singleton creation
        if not self.topic:
            self.topic = os.getenv("NTFY_TOPIC")
            self.server = os.getenv("NTFY_SERVER", "https://ntfy.sh").rstrip("/")

        if not self.topic:
            print("[NtfyBridge] NTFY_TOPIC not set in environment. Ntfy integration disabled.")
            return

        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        print(f"[NtfyBridge] Listening to ntfy topic: {self.topic} on {self.server}")

    def stop(self):
        self.running = False

    def _listen_loop(self):
        url = f"{self.server}/{self.topic}/json"
        
        while self.running:
            try:
                # SSE streaming connection
                resp = requests.get(url, stream=True, timeout=60)
                if resp.status_code == 200:
                    for line in resp.iter_lines():
                        if not self.running:
                            break
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8'))
                                if data.get('event') == 'message':
                                    self._handle_message(data)
                            except json.JSONDecodeError:
                                pass
                else:
                    time.sleep(5)
            except requests.exceptions.RequestException:
                time.sleep(5)
            except Exception as e:
                print(f"[NtfyBridge] Unexpected error: {e}")
                time.sleep(10)

    def _handle_message(self, data):
        message = data.get('message', '')
        title = data.get('title', '')
        # Construct a formatted text block
        text_parts = []
        if title:
            text_parts.append(f"{title}:")
        if message:
            text_parts.append(message)
            
        full_text = " ".join(text_parts).strip()
        
        if full_text:
            with self._lock:
                self.messages.append({
                    "text": full_text,
                    "title": title,
                    "raw_message": message,
                    "id": data.get('id'),
                    "timestamp": data.get('time')
                })

    def get_messages(self, limit=10):
        with self._lock:
            msgs = self.messages[:limit]
            self.messages = self.messages[limit:]
            return msgs

def start_ntfy_bridge():
    bridge = NtfyBridge.get_instance()
    bridge.start()
    return bridge

def stop_ntfy_bridge():
    bridge = NtfyBridge.get_instance()
    bridge.stop()
