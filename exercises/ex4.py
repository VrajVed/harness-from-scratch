import json
from llm import chat
from exercises.ex3 import TOOLS, TOOL_SCHEMAS, execute_tool

MAX_STEPS = 10
MAX_TOOL_CHARS = 4_000

def truncate(text: str, limit: int = MAX_TOOL_CHARS) -> str:

    if len(text) <= limit:
        return text

    half = limit // 2

    dropped = len(text) - limit

    return (text[:half] + f"\n\n... [{dropped} characters truncated] ...\n\n" + text[-half:])


def context_size(messages: list[dict]) -> int:

    total = 0

    for message in messages:
        total += len(str(message.get("content") or ""))

        for call in message.get("tool_calls") or []:
            total += len(call["function"]["arguments"])

    return total


def read_lines(path: str, start: int, end: int) -> str:
    
    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.readlines()

    return "".join(lines[start - 1:end])


def run(task: str) -> None:
    messages = [
        {"role" : "system", "content": "Use tools to complete the task"},
        {"role": "user", "content": task},
    ]

    for step in range(MAX_STEPS):

        message = chat(messages, tools=TOOL_SCHEMAS)
        messages.append(message)

        print(f"[step {step}] context: {context_size(messages)} chars")

        tool_calls = message.get("tool_calls") or []

        if not tool_calls:
            print(f"final answer: {message['content']}")

            return

        for call in tool_calls:

            result = execute_tool(
                call["function"]["name"],
                call["function"]["arguments"],
            )

            result = truncate(result)

            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": result,
            })


if __name__ == "__main__":
    run("Read big.txt and tell me exactly what word is on line 12345")

