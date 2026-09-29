import json
import random
import time
import urllib.request
from exercises.ex5 import STATE, log_step
from llm import BASE_URL, API_KEY, MODEL, LLMError, chat
from exercises.ex3 import TOOLS, TOOL_SCHEMAS, execute_tool

MAX_STEPS = 10

RETRYABLE = {
    429,
    500,
    502,
    503,
    529
}


def chat_with_retry(
        messages: list[dict],
        tools: list[dict] | None = None,
        max_attempts: int = 4  
    ) -> dict:

    for attempt in range(1, max_attempts + 1):
        try:
            
            return chat(messages, tools)
        
        except LLMError as error:
            if error.status not in RETRYABLE or attempt == max_attempts:
                raise 
            
            delay = 2 ** (attempt - 1) + random.uniform(0, 1)

            print(f"HTTP {error.status} - retrying in {delay:.1f}s", f"attempt {attempt}/{max_attempts})")
            time.sleep(delay)


def chat_stream(messages: list[dict]) -> str:

    payload = {
        "model": MODEL,
        "message": messages,
        "temperature": 0.0,
        "stream": True,
    }

    request = urllib.request.Request(
        url=f"{BASE_URL}/chat/completions",
        data= json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
    )

    full_text = ""
    
    with urllib.request.urlopen(request, timeout=60) as response:
        for raw_line in response:
            line = raw_line.deconde("utf-8").strip()
            if not line.startswith("data:"):
                continue

            data = line[len("data: "):]

            if data == "[DONE]":
                break

            delta = json.loads(data)["choices"][0].get("delta", {})

            token = delta.get("content") or ""
            print(token, end="", flush=True)
            full_text += token

        print()
        return full_text

def run(task: str) -> None:
    messages = [{"role": "user", "content": task}]

    for step in range(MAX_STEPS):
        message = chat_with_retry(messages, tools=TOOL_SCHEMAS)
        messages.append(message)

        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            chat_stream(messages)   # stream the final answer live
            return

        for call in tool_calls:
            name = call["function"]["name"]
            result = execute_tool(name, call["function"]["arguments"])
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": result,
            })

    print(f"hit MAX_STEPS={MAX_STEPS}")

    

if __name__ == "__main__":
    run("Explain in two sentences why retries need jitter.")

