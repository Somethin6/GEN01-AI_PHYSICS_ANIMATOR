import httpx, json, os, time
from typing import List, Dict, Optional, Iterator

class LLM:
    def __init__(self, host: str, model: str, temperature: float, top_p: float, max_tokens: int, stop: List[str]):
        self.host = host.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.stop = stop or []

    def chat(self, messages: List[Dict[str, str]]) -> str:
        # Ollama /api/chat
        payload = {
            "model": self.model,
            "messages": messages,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_predict": self.max_tokens,
            },
            "stop": self.stop,
            "stream": False,
        }
        timeout = float(os.getenv("LLM_HTTP_TIMEOUT", "600"))
        last_exc = None
        for attempt in range(3):
            try:
                with httpx.Client(timeout=timeout) as client:
                    r = client.post(f"{self.host}/api/chat", json=payload)
                    r.raise_for_status()
                    data = r.json()
                    return data.get("message", {}).get("content", "")
            except Exception as e:
                last_exc = e
                time.sleep(1 + attempt)
        raise last_exc

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_predict": self.max_tokens,
            },
            "stop": self.stop,
            "stream": False,
        }
        timeout = float(os.getenv("LLM_HTTP_TIMEOUT", "600"))
        last_exc = None
        for attempt in range(3):
            try:
                with httpx.Client(timeout=timeout) as client:
                    r = client.post(f"{self.host}/api/generate", json=payload)
                    r.raise_for_status()
                    data = r.json()
                    return data.get("response", "")
            except Exception as e:
                last_exc = e
                time.sleep(1 + attempt)
        raise last_exc

    def chat_stream(self, messages: List[Dict[str, str]]) -> Iterator[str]:
        payload = {
            "model": self.model,
            "messages": messages,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_predict": self.max_tokens,
            },
            "stop": self.stop,
            "stream": True,
        }
        timeout = float(os.getenv("LLM_HTTP_TIMEOUT", "600"))
        with httpx.Client(timeout=timeout) as client:
            with client.stream("POST", f"{self.host}/api/chat", json=payload) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                    except Exception:
                        continue
                    if ev.get("done"):
                        break
                    delta = ev.get("message", {}).get("content", "")
                    if delta:
                        yield delta

    def generate_stream(self, prompt: str) -> Iterator[str]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_predict": self.max_tokens,
            },
            "stop": self.stop,
            "stream": True,
        }
        timeout = float(os.getenv("LLM_HTTP_TIMEOUT", "600"))
        with httpx.Client(timeout=timeout) as client:
            with client.stream("POST", f"{self.host}/api/generate", json=payload) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                    except Exception:
                        continue
                    if ev.get("done"):
                        break
                    delta = ev.get("response", "")
                    if delta:
                        yield delta
