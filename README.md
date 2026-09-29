# harness-from-scratch

Build an AI agent harness from first principles — no LangChain, no agents SDK, no `openai` package. Just Python stdlib and the raw HTTP protocol.

An LLM is a stateless text completer. The **harness** is everything around it that turns it into a stateful, tool-using, error-recovering agent: memory, tool dispatch, validation, context budgets, termination, retries, streaming. These six exercises build each layer by hand so you understand what the frameworks are hiding.

## Prerequisites

- Python 3.10+
- A [Groq](https://console.groq.com) API key (free tier works — you'll even hit real 429s, which is one of the lessons)

## Setup

```bash
git clone https://github.com/VrajVed/harness-from-scratch.git
cd harness-from-scratch
cp .env.example .env     # then paste your key into .env
```

`.env` looks like:

```bash
GROQ_API_KEY=gsk_your-key-here
MODEL=llama-3.3-70b-versatile
```

No dependencies to install. Verify the client works:

```bash
PYTHONPATH=. python3 -c "from llm import chat; print(chat([{'role':'user','content':'say OK'}])['content'])"
# Expected: OK
```

## The Exercises

Run everything from the repo root with `PYTHONPATH=.` so `llm.py` is importable:

| # | File | You build | The lesson |
|---|------|-----------|------------|
| 1 | `exercises/ex1.py` | Stateful chat loop | The model has no memory. **You** are the memory. |
| 2 | `exercises/ex2.py` | One tool, hand dispatch | Tool calling is a protocol: structured request out, structured result in. |
| 3 | `exercises/ex3.py` | Multi-tool router + validation | The dispatcher is a trust boundary. The model is an untrusted caller. |
| 4 | `exercises/ex4.py` | Truncation + precision tools | Context is a budget. Tool design follows context policy. |
| 5 | `exercises/ex5.py` | Stop conditions + flight recorder | The model suggests; the harness disposes. |
| 6 | `exercises/ex6.py` | Retry with jitter + SSE streaming | Reliability is a policy layer, not model behavior. |

```bash
PYTHONPATH=. python3 exercises/ex1.py
PYTHONPATH=. python3 exercises/ex2.py
# ... and so on
```

**Do them in order.** Each one reuses the previous exercise's code. And when something breaks — it will — read the traceback before reaching for a fix. Every bug in these exercises is a real failure mode production harnesses have.

## Repo layout

```
harness-from-scratch/
├── .env.example       # copy to .env, add your Groq key
├── llm.py             # the HTTP client — .env loader, chat(), LLMError
└── exercises/
    ├── ex1.py         # memory: the stateful loop
    ├── ex2.py         # tools: the 4-step dance
    ├── ex3.py         # router: validate → execute → wrap errors
    ├── ex4.py         # budget: truncate + read_lines precision tool
    ├── ex5.py         # termination: finish tool + trajectory.jsonl
    └── ex6.py         # reliability: retry/backoff + SSE streaming
```

## Common pitfalls

- **`ModuleNotFoundError: No module named 'llm'`** — you ran from inside `exercises/` or forgot `PYTHONPATH=.`. Run from the repo root.
- **`KeyError: 'GROQ_API_KEY'`** — `.env` is missing, misnamed, or the key line has a typo.
- **HTTP 400 with `tool_use_failed`** — the model emitted malformed tool-call arguments (happens with smaller models). That's not your bug; it's what retry/validation layers exist for.
- **HTTP 429** — free-tier rate limit. Expected. Exercise 6 is literally about surviving it.

## What this is (and isn't)

This is a **learning resource**, not a framework. The code is deliberately small and dependency-free so every line is legible. If you want production agent infrastructure, look at what Claude Code, MCP servers, and the OpenAI Agents SDK do — you'll now recognize every layer.

## License

MIT
