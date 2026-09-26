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
            "properties": {"path"}
        }
    }
}