# importing our llm module

from llm import chat


# We basically give our system prompt right here

SYSTEM_PROMPT = "You are a concise assistant that gets straight to the point, answer in one sentence."

MAX_TURNS = 3 # Max turns of converstation

def main() -> None:

    history = [{
        "role": "system",
        "content": SYSTEM_PROMPT
    }]

    for turn in range(1, MAX_TURNS + 1):

        user_text = input(f"[turn {turn}] You: ")

        history.append({
            "role": "user",
            "content": user_text
        })

        reply = chat(history) # giving the whole history

        history.append(reply) # giving model replies to itself in the history

        print(f"[turn {turn}] Assistant: {reply['content']}\n")


    print("----final-history----")

    for message in history:

        print(f"{message['role']:>9}: {str(message['content'])[:60]}")


if __name__ == "__main__":
    main()


