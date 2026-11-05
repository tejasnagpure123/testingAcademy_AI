from dotenv import load_dotenv
from langchain.agents import create_agent
import os

load_dotenv()


def main():
    print("Creating Your first Langchain agent...\n")
    agent = create_agent(model=os.getenv("GEMINI_LLM_MODEL"))
    query = input("Ask Your Question")
    print("Streaming response")

    for token, metadata in agent.stream(
        {
            "messages": [
                {"role": "system", "content": "You are software engineer"},
                {"role": "user", "content": query},
            ]
        },
        stream_mode="messages",
    ):
        print(token.text, end="", flush=True)

    print()


if __name__ == "__main__":
    main()
