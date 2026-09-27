# Test Ananlyst Agent
#
# a senior QA with 15 years (JIRA MD)
#  of experience. Based on the feature,
# it will just analyze the requirement
# and suggest a 5-10 testcases(p0 testcases).

from crewai import Agent, Task, Crew, LLM
from dotenv import load_dotenv
import os
from pathlib import Path

# By Default crew AI actually the brain which
# OpenAI - GROQ API Key


# Step 0 - Set up the Brain
# Step 1. - Define the Agent (identity)
# Step 2. - Give the Task to the Agent
# Step 3. Add them to the Crew
# Step 4. Kick Off Agent.

# Prompt vs Skill vs AI Agent

# We need use the GROQ gpt-oss-120b model


# Step 0 - Set up the Brain (Groq LLM)
load_dotenv(Path(__file__).with_name(".env"))

# Groq exposes an OpenAI-compatible API, so we use the "openai/" provider
# prefix with a custom base_url pointing at Groq.
model_name = os.getenv("GROQ_MODEL")
api_key = os.getenv("GROQ_API_KEY")
base_url = os.getenv("BASE_URL")

missing_settings = [
    name
    for name, value in (
        ("GROQ_MODEL", model_name),
        ("GROQ_API_KEY", api_key),
        ("BASE_URL", base_url),
    )
    if not value
]
if missing_settings:
    raise RuntimeError(
        f"Missing required settings in Chapter012Crew.ai/.env: {', '.join(missing_settings)}"
    )

if not model_name.startswith("openai/"):
    model_name = f"openai/{model_name}"

groq_llm = LLM(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
)

# Step 1. - Define the Agent (identity)
qa_agent = Agent(
    role="QA Engineer",
    goal="Analyze the feature or requirements and create 5-10 high-priority test cases.",
    backstory="You are a senior QA engineer with 15 years of experience in test planning and test case creation.",
    llm=groq_llm,
    verbose=True,
)

# Step 2 - Give the Task to the Agent
test_case_task = Task(
    description=(
        "Create 5-10 high-priority test cases for the app.vwo.com login page. "
        "It has username, password, submit, and remember-me functionality. "
        "For each case, include a title, preconditions, steps, and expected result."
    ),
    expected_output="A numbered list of 5-10 test cases with steps and expected results.",
    agent=qa_agent,
)

# Step 3. Add them to the Crew
crew = Crew(agents=[qa_agent], tasks=[test_case_task], verbose=True)

# Step 4. Kick off the crew
if __name__ == "__main__":
    result = crew.kickoff()
    print(result)
