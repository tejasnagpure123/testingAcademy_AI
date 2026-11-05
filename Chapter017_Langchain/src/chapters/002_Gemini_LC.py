from dotenv import load_dotenv
from langchain.agents import create_agent
import os

load_dotenv()


def main():
    print("Creating Your first Langchain agent...\n")
    agent = create_agent(model=os.getenv("GEMINI_LLM_MODEL"))
    query = input("Ask Your Question")
    result = agent.invoke({"messages": [{"role": "user", "content": query}]})

    final_message = result["messages"][-1]
    content = final_message.content
    if isinstance(content, list):
        answer = "".join(
            block["text"] for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    else:
        answer = content
    print(answer)


if __name__ == "__main__":
    main()
