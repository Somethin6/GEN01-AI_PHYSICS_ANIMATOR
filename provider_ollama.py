import requests, json


class OllamaLLM:
    def __init__(self, model="qwen2.5:14b-instruct-q4_K_M", host="http://127.0.0.1:11434"):
        self.model = model
        self.host = host.rstrip("/")

    def chat(self, system, user, temperature=0.4, max_tokens=2048):
        url = f"{self.host}/api/chat"
        payload = {
            "model": self.model,
            "options": {"temperature": temperature, "num_predict": max_tokens},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        }
        r = requests.post(url, json=payload, timeout=1200)
        r.raise_for_status()
        data = r.json()
        return data.get("message", {}).get("content", "")
