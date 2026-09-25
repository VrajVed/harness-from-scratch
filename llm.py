import json
import os
import urllib.request
import urllib.error

def load_env(path: str = ".env") -> None:

    try:
        with open(path, "r", encoding="utf-8") as handle:
            lines = handle.readlines()

    except FileNotFoundError:
        return

    for line in lines:

        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, _, value = line.partition("=")

        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()

BASE_URL = os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

API_KEY = os.environ["GROQ_API_KEY"]

MODEL = os.environ.get("MODEL", "llama-3.3-70b-versatile")

class LLMError(Exception):

    def __init__(self, status: int, detail: str):
        self.status = status

        super().__init__(f"HTTP {status}: {detail}")


def chat(messages: list[dict], tools: list[dict] | None = None) -> dict:

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.0
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    request = urllib.request.Request(
        url = f"{BASE_URL}/chat/completions",
        data =json.dumps(payload).encode("utf-8"),
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
            "User-Agent": "groq-python/0.1.0"
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    
    except urllib.error.HTTPError as error:

        detail = error.read().decode("utf-8")
        raise LLMError(error.code, detail) from error

    return body["choices"][0]["message"]

