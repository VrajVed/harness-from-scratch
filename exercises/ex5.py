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
    "description" : "Call this when the task is fully complete, with the final answer.",
    "schema" : {
        "type" : "object",
        "properties" : {
            "answer" : {
                "type" : "string",
            }
        },
        "required" : ["answer"]
    }
}

TOOL_SCHEMAS.append({
    "type": "function", "function": {
        "name": "finish",
        "description": TOOLS["finish"]["description"],
        "parameters": TOOLS["finish"]["schema"],
    },
})

def log_step(record: dict) -> None:

    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")

def run(task: str) -> None:

    messages = [
        {"role": "system", "content":
            "Use tools to complete the task. Call finish(answer) when done."},
        {"role": "user", "content": task},
    ]

    for step in range(MAX_STEPS):

        message = chat(messages, tools=TOOL_SCHEMAS)

        messages.append(message)

        record = {"step": step,
                  "assistant": message.get("content"),
                  "tool_calls": [], "results": []}

        for call in message.get("tool_calls") or []:
            
            name = call["function"]["name"]
            
            result = execute_tool(name, call["function"]["arguments"])
            
            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": result,
            
            })
            
            record["tool_calls"].append(name)
            record["results"].append(result[:200])

        
        record["finished"] = STATE["done"]
        
        log_step(record)

        if STATE["done"]:
            print(f"[step {step}] finished: {STATE['answer']}")
            return

        
        if not message.get("tool_calls"):                  
            print(f"[step {step}] no tool calls and no finish — stuck")
            return

    print(f"hit MAX_STEPS={MAX_STEPS}")                     

if __name__ == "__main__":
    run("Create a file called DONE containing the word 'complete', "
        "then finish.")

    