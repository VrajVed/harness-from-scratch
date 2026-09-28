import json
from llm import chat
from exercises.ex3 import TOOLS, TOOL_SCHEMAS, execute_tool

MAX_STEPS = 10
LOG_PATH = "ex5.jsonl"

STATE = {
    "done": False,
    "answer": None,
}

def finish(answer: str) -> str:
    STATE["done"] = True
    STATE["answer"] = answer 

    return "task marked complete"

TOOLS["finish"] = {
    "function" : finish,
    "description" : "Ca"
}