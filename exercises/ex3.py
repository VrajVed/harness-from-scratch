import json
import os
from llm import chat

MAX_STEPS = 10

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()

def write_file(path: str, content: str) -> str:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
        return f"Wrote {len(content)} characters to {path}"

def list_dir(path: str = ".") -> str:
    return "\n".join(sorted(os.listdir(path)))


TOOLS = {
    "read_file" : {
        "function": read_file,
        "description": "Read the contents of a file",
        "schema" : {
            "type" : "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        }
    },
    "write_file" : {
        "function": write_file,
        "description": "Write content to a file",
        "schema" : {
            "type" : "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"]
        }
    },
    "list_dir" : {
        "function": list_dir,
        "description": "List the contents of a directory",
        "schema" : {
            "type" : "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]
        }
    }
}

TOOL_SCHEMAS = [{
    "type": "function",
    "function" : {
        "name": name,
        "description": tool["description"],
        "parameters" : tool["schema"]
    }}
     
     for name, tool in TOOLS.items()
]

def validate(schema: dict, arguments: dict) -> list[str]:

    problems = []

    for key in schema.get("required", []):
        if key not in arguments:
            problems.append(f"Missing required argument '{key}'")

            for key,value in arguments.items():
                if key not in schema.get("properties", {}):
                    problems.append(f"Unexpected argument '{key}'")

                elif schema["properties"][key]["type"] == "string" and not isinstance(value, str):
                    problems.append(f"Argument '{key}' should be a string")

    return problems

def execute_tool(name: str, arguments_json: str) -> str:

    tool = TOOLS.get(name)

    if tool is None:
        return f"Error - Unknown Tool '{name}'. Available tools: {sorted(TOOLS)}"

    try: 
        arguments = json.loads(arguments_json)

    except json.JSONDecodeError:
        return f"Error - Arguments are not valid, Invalid JSON: {arguments_json}"

    problems = validate(tool["schema"], arguments)
    if problems:
        return f"Error - Arguments are not valid: {', '.join(problems)}"

    try:
        return str(tool["function"](**arguments))

    except Exception as error:

        return f"Error: {type(error).__name__} - {error}"


def run(task: str) -> None:
    messages = [
        {"role": "system", "content": "Use tools to complete the task."},
        {"role": "user", "content": task},
    ]
    for step in range(MAX_STEPS):
        message = chat(messages, tools=TOOL_SCHEMAS)
        messages.append(message)

        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            print(f"[step {step}] final answer: {message['content']}")
            return

        for call in tool_calls:
            result = execute_tool(
                call["function"]["name"],
                call["function"]["arguments"],
            )
            print(f"[step {step}] {call['function']['name']} → {result[:70]}")
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": result,
            })


if __name__ == "__main__":
    run("List the files here, read the first .py file you find, "
        "and write its line count into size.txt")