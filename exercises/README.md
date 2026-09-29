# The Exercises, In Depth

Each exercise teaches one layer of the harness. For each: the concept, what to do, experiments to break it on purpose, how to verify it worked, and the intuition to take away.

**General rules:**

- Run everything from the repo root: `PYTHONPATH=. python3 exercises/exN.py`
- Do them in order — ex3 reuses ex2's loop, ex4 reuses ex3's router, and so on.
- The experiments are not optional. Reading code teaches syntax. Breaking code teaches systems.

---

## Exercise 1 — The Memory Is You

**Concept.** The API is stateless. Every call is a pure function: messages in, reply out. The server remembers nothing. If you want the model to "remember" turn 1 during turn 3, *you* must resend turn 1 inside the `messages` array. That array **is** the agent's memory, and it lives in your process.

The array grows like this:

```
turn 1:  [system, user₁]                      → assistant₁
turn 2:  [system, user₁, assistant₁, user₂]   → assistant₂
```

**Do this.** Run ex1 and have the 3-turn conversation:

```bash
PYTHONPATH=. python3 exercises/ex1.py
# You: My name is <your name>.
# You: What is my name?
# You: What is 2+2?
```

**Experiments.**

- *Amnesia:* comment out the line that appends the assistant's reply to history. Rerun. On turn 2 the model will deny knowing your name — even though it answered you last turn. You just proved statelessness empirically.
- *String mush:* try replacing the message list with one big concatenated string. It "works" but the model can no longer tell its words from yours. This is why structured messages exist.

**Verified when:** turn 2's reply contains your name, turn 3's contains "4".

**Takeaway:** context is state. Whoever owns the array owns the memory. Later — truncation, summarization, forking — it's all memory management, exactly like an OS.

---

## Exercise 2 — The Model Asks, You Execute

**Concept.** Tool calling is not the model running code. The model can only emit *text structured as a request*:

```json
{"name": "get_time", "arguments": "{}"}
```

Your code parses that, decides whether to honor it, runs the actual Python function, and appends the result as a `role: "tool"` message. The full cycle:

```
1. you → model:  conversation + tool schemas ("here's what exists")
2. model → you:  tool_calls ("please run get_time")
3. you → model:  tool result message ("get_time returned 2026-09-29T14:30")
4. model → you:  final answer ("It's 2:30 PM.")
```

**Do this.** Run ex2:

```bash
PYTHONPATH=. python3 exercises/ex2.py
```

**Experiments.**

- *Missing result:* execute the tool but don't append the result message. The model will call the tool forever — it asked a question you never answered.
- *Lying description:* change the tool's description to "Get the current weather." Watch the model call it for weather queries and trust the ISO timestamp as weather. The model believes schemas more than users.

**Verified when:** you see one `model requested: get_time(...)` line, then a final answer containing today's date.

**Takeaway:** tool calling is just a protocol. Structured request out, structured result in. The "magic" is the schema and the loop.

---

## Exercise 3 — The Router Is a Trust Boundary

**Concept.** The model is an untrusted caller of your functions. Eventually it will: emit malformed JSON, invent arguments, call tools that don't exist, and pass paths that don't exist. All four failure classes must become **tool-result strings** — never exceptions that kill your loop.

Why? Because an error *inside the conversation* is an observation the model can recover from. A crash is not. When `read_file("/nope.txt")` returns `ERROR: FileNotFoundError`, the model reads it, adjusts, and tries listing the directory instead. That's self-correction — and all you did was not die.

**Do this.** Run ex3:

```bash
PYTHONPATH=. python3 exercises/ex3.py
cat size.txt   # should contain a number
```

**Experiments.**

- *Recovery:* ask it to read a file that doesn't exist. Watch it receive the error, call `list_dir`, find a real file, and continue.
- *Validation bite:* the `validate()` function catches missing/extra/mistyped arguments *before* execution and sends the complaint back as a tool result. The model fixes its own call.

**Verified when:** `size.txt` exists with a number in it.

**Takeaway:** everything the model emits is hostile input until validated; every outcome — success or failure — is just text going back into context. This one dispatcher function is most of what "agent reliability" means in practice.

---

## Exercise 4 — Context Is a Budget

**Concept.** The context window is finite, and every token in it costs money and latency on every call. One `read_file` on a big log can return megabytes — instant overflow.

The harness's answer is a **truncation policy**: keep the head (headers, schema, first records) and the tail (recent lines, the actual error), drop the middle — *with a marker* so the model knows data is missing. And here's the deep part: once the middle is missing, the model needs a **precision tool** (`read_lines(path, start, end)`) to fetch exactly what was cut. Tool design follows context policy.

**Do this.** Generate the big file, then run ex4:

```bash
python3 -c "print('\n'.join(f'word-{i}' for i in range(1, 20001)))" > big.txt
PYTHONPATH=. python3 exercises/ex4.py
```

**Experiments.**

- *Silent truncation:* remove the `[N characters truncated]` marker (just cut the text). The model no longer knows data is missing and answers confidently from the head. The marker is what keeps truncation honest.
- *Budget watch:* shrink `MAX_TOOL_CHARS` to 500 and watch the context-size print stay flat while the model makes more, smaller calls. Policy shapes behavior.

**Verified when:** the final answer is exactly `word-12345`, fetched via `read_lines`, not guessed.

**Takeaway:** the harness is the memory manager. Context is RAM, truncation is paging, precision tools are the syscall interface for what got paged out.

---

## Exercise 5 — The Harness Owns Termination

**Concept.** Left alone, a model in a loop never stops — there's always something it could do next. Termination is external to the model. Three kinds:

1. **Budget:** `MAX_STEPS` — the circuit breaker. Always present, always last resort.
2. **State-based:** a file exists, a test passes. The environment decides.
3. **Model-declared:** the model calls a `finish(answer)` tool. A tool call is an unambiguous protocol signal — far better than parsing "DONE" out of prose.

While you're at it, ex5 adds the **flight recorder**: one JSON line per step to `ex5.jsonl`. When the agent misbehaves at step 7, you don't guess — you replay.

**Do this.**

```bash
PYTHONPATH=. python3 exercises/ex5.py
cat DONE          # should contain "complete"
cat ex5.jsonl     # one JSON object per step
```

**Experiments.**

- *Text-DONE vs finish-tool:* remove the finish tool, tell the model to "say DONE when finished." Count how often it says DONE mid-task, or never says it. Now you know why the submit pattern exists.
- *Replay:* read `ex5.jsonl` and reconstruct exactly what the model saw at each step. If you can't, your logging is insufficient — fix it.

**Verified when:** `DONE` exists, the loop stops in ≤3 steps via the finish call, and the JSONL has a record per step.

**Takeaway:** the model suggests; the harness disposes. Termination and observability are harness concerns — the model doesn't even know they're happening.

---

## Exercise 6 — Failure Is Normal

**Concept.** Production LLM calls fail routinely: rate limits (429), overloaded servers (503), dropped connections. The retry policy:

- **Retry only transient errors** (429, 5xx). A 400 is *your* bug — retrying it just pays for the same error twice.
- **Exponential backoff with jitter:** wait `2^attempt + random` seconds. Without jitter, thousands of clients retry in lockstep and re-crush the server.
- **Retries are safe because the call is pure.** All state lives in your `messages` list — resending it changes nothing server-side.

Streaming is separate: instead of waiting for the whole reply, the server sends Server-Sent Events — lines of `data: {json}` ending with `data: [DONE]`. One real-world subtlety: streaming + tool calls is fiddly (arguments arrive fragmented across chunks), which is why harnesses stream **only the final user-facing answer** and keep the tool loop non-streaming.

**Do this.**

```bash
PYTHONPATH=. python3 exercises/ex6.py
```

**Experiments.**

- *Force a retry:* point `GROQ_BASE_URL` at a dead port (`GROQ_BASE_URL=http://localhost:9 PYTHONPATH=. python3 exercises/ex6.py`), or just run the loop a few times — the free tier will 429 you for real. Watch backoff kick in.
- *Retry a 400:* send a deliberately broken payload through the retry wrapper. It should fail immediately, not 4 times.

**Verified when:** the final answer streams token by token, and any 429s show up as retry lines without killing the loop.

**Takeaway:** reliability is a policy layer, not model behavior. The model knows nothing about your retries, your backoff, your streams.

---

## After the six

You now own every layer: memory, tools, routing, context budgets, termination, observability, reliability. Assemble them into one `my_harness/` directory — `llm.py`, `tools.py`, `memory.py`, `loop.py` — and point it at one real task from your life. When it completes a real task end to end, you have a from-scratch harness and, more importantly, the intuition to know when a workflow needs one.
