# harness-from-scratch

You keep hearing about AI agents. Models that read files, run commands, browse the web, fix bugs. But here's the thing: **the model itself does none of that.** A language model is a stateless function, text in, text out. It has no memory between calls, it can't touch your filesystem, it can't even call a function by itself.

What makes it an "agent" is the **harness**: the code around the model that remembers the conversation, executes the tools the model asks for, feeds results back, decides when to stop, and retries when the network flakes.

Frameworks like LangChain hide all of this behind abstractions. This repo builds it by hand, six exercises, pure Python stdlib, no dependencies. By the end, you'll have written every layer of a working agent loop yourself, and every framework will look like what it actually is: this loop plus bookkeeping.

## What you'll build

A program that does this:

```
You:    "Create a file called hello.txt with 'world' inside, then verify it."
Model:  → requests write_file("hello.txt", "world")
Code:   → executes it, returns "wrote 5 chars"
Model:  → requests read_file("hello.txt")
Code:   → executes it, returns "world"
Model:  "Done, the file contains 'world'."
```

The model never touched your disk. Your harness did, because the model asked it to, in JSON.

## Setup (5 minutes)

**1. Get a free Groq API key.** Sign up at [console.groq.com](https://console.groq.com), go to API Keys, create one. It starts with `gsk_`.

**2. Clone and configure:**

```bash
git clone https://github.com/VrajVed/harness-from-scratch.git
cd harness-from-scratch
cp .env.example .env
```

Open `.env` and paste your key:

```bash
GROQ_API_KEY=gsk_your-actual-key-here
MODEL=llama-3.3-70b-versatile
```

**3. Verify it works** (no dependencies to install, Python 3.10+ only):

```bash
PYTHONPATH=. python3 -c "from llm import chat; print(chat([{'role':'user', 'content':'say OK'}])['content'])"
```

You should see `OK`. If you see `KeyError: 'GROQ_API_KEY'`, your `.env` file is missing or the key line is misspelled.

## The exercises

Run each from the repo root, in order. Each builds on the last.

```bash
PYTHONPATH=. python3 exercises/ex1.py
```

| # | Exercise | You build | What clicks |
|---|----------|-----------|-------------|
| 1 | [ex1.py](exercises/ex1.py) | A chat loop that remembers | The model forgets everything between calls. **You** resend the whole conversation every time. |
| 2 | [ex2.py](exercises/ex2.py) | One tool (`get_time`) | The model doesn't run code, it *requests* it in JSON. You decide whether to obey. |
| 3 | [ex3.py](exercises/ex3.py) | 3 tools + input validation | The model is an untrusted caller. Malformed JSON, wrong args, nonexistent files, all become error strings, never crashes. |
| 4 | [ex4.py](exercises/ex4.py) | Truncation + a precision tool | Context windows overflow. Truncate tool output, and the model learns to ask for specific line ranges. |
| 5 | [ex5.py](exercises/ex5.py) | A `finish()` tool + logging | Left alone, the loop never stops. Termination is the harness's job, not the model's. |
| 6 | [ex6.py](exercises/ex6.py) | Retry with backoff + streaming | 429s and 503s are normal. Retry transient errors, stream the final answer token by token. |

### What a good run looks like

Exercise 2, start to finish:

```bash
$ PYTHONPATH=. python3 exercises/ex2.py
[step 0] model requested: get_time({})
[step 1] final answer: It's currently 2026-09-26 12:02:30.193066 (local time).
```

Step 0: the model emitted a `tool_calls` request instead of text. Your code executed `get_time()` and appended the result. Step 1: the model read the result and answered. That request → execute → result → answer cycle is the entire foundation, every agent framework is this loop plus bookkeeping.

**Expect bugs.** The point isn't to copy-paste working code, it's to watch each layer fail and understand why. When your agent hallucinates a file path (it will), or the model emits garbage tool arguments (it does), you're seeing real failure modes that production harnesses handle every day.

## Repo layout

```
harness-from-scratch/
├── .env.example        # copy to .env, paste your Groq key
├── llm.py              # the HTTP client: .env loader, chat(), LLMError
└── exercises/
    ├── README.md       # per-exercise deep dives: concepts, experiments, pitfalls
    ├── ex1.py          # memory: the stateful loop
    ├── ex2.py          # tools: the 4-step request/execute/result/answer dance
    ├── ex3.py          # router: validate → execute → wrap errors as strings
    ├── ex4.py          # budget: truncate + read_lines precision tool
    ├── ex5.py          # termination: finish tool + trajectory.jsonl flight recorder
    └── ex6.py          # reliability: retry/backoff + SSE streaming
```

## Common pitfalls

- **`ModuleNotFoundError: No module named 'llm'`**: run from the repo root with `PYTHONPATH=.`, not from inside `exercises/`.
- **`KeyError: 'GROQ_API_KEY'`**: `.env` missing, misnamed, or the key line has a typo.
- **HTTP 400 `tool_use_failed`**: the model emitted malformed tool arguments (common with smaller models). Not your bug; this is why validation layers exist.
- **HTTP 429**: free-tier rate limit. Exercise 6 is literally about surviving this.
- **Step 0 prints, then silence**: your loop is missing the "no tool calls → print answer and return" branch.

## What this is (and isn't)

A **learning resource**, not a framework. The code is deliberately small and dependency-free so every line is legible. After this, when you look at Claude Code, MCP servers, or the OpenAI Agents SDK, you'll recognize every layer, because you built each one.

## License

MIT, take it, break it, teach with it.
