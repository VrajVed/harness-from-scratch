from datetime import datetime
from llm import chat

MAX_STEPS = 5

def get_time() -> str:

    return datetime.now().isoformat()

TOOLS = {
    "get_time" : get_time
}

TOOL_SCHEMAS = [{
    "type": "function",
    "function" : {
        "name": "get_time",
        "description": "Get current local date and time in  iso format",
        "parameters" : {
            "type": "object",
            "properties": {},
        }
    }
}]

def run(task: str) -> None:

    messages = [
        {"role": "system", "content": "Use tools when you need real-world data."},
        {"role": "user", "content": task}
    ]

    for step in range(MAX_STEPS):

        message = chat(messages, tools=TOOL_SCHEMAS)

        messages.append(message)

        tool_calls = message.get("tool_calls") or []

        if not tool_calls:
            print(f"[step {step}] final answer: {message['content']}")
            return

        for call in tool_calls:

            name = call["function"]["name"]

            print(f"[step {step}] model requested: {name}({call['function']['arguments']})")

            result = TOOLS[name]()

            messages.append({
                "role" : "tool",
                "tool_call_id": call["id"],
                "content": result,
            })

    print("hit MAX_STEPS without a final answer")

if __name__ == "__main__":
    run("What time is it now ?")

