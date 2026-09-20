#test analyst ai agent

# A senior QA with 15 years of experience(JIRA md)
# Based on the feature it will just analyse the requirement
# and suggest 5-10 test cases

from crewai import Agent, Task, Crew
from crewai import LLM
from dotenv import load_dotenv
import os
import sys
import litellm

# Force UTF-8 encoding for Windows console to prevent UnicodeEncodeError on print
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Monkey patch litellm to strip cache_breakpoint which crewai injects but groq doesn't support
original_completion = litellm.completion
def patched_completion(*args, **kwargs):
    if "messages" in kwargs:
        for msg in kwargs["messages"]:
            msg.pop("cache_breakpoint", None)
    return original_completion(*args, **kwargs)
litellm.completion = patched_completion

# By default crew ai uses OPEN ai as its brain 
# But we will use GROQ as its brain

#Step 0: Set up the brain
#Step 1: Define the agent identity
#Step 2: Give the task to agent
#Step 3: Add them to the Crew
#Step 4: Kick off the agent

#We need to use gpt-oss-120b model of GROQ


#Step 0: Set up the brain
load_dotenv()
groq_llm = LLM(
    model=os.getenv("GROQ_MODEL", "groq/gpt-oss-120b"),
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("BASE_URL")
)

#Step 1: Define the agent identity
qa_agent= Agent(
    role='Senior QA Engineer',
    goal="Based on the feature it will just analyse the requirement and suggest 5-10 test cases",
    backstory="You are a senior QA with 15 years of experience. You have worked on various projects and have a good understanding of different testing methodologies. You are also a good communicator and can explain complex concepts in a simple way.",
    verbose=True,
    llm=groq_llm,
    cache=False
)

#Step 2: Give the task to agent
test_case_task= Task(
    description="Create 5-10 Test cases",
    expected_output="A numbered list of 5-10 test cases with a bried description of app.vwo.com Login page with the username, password and submit button with remember me functionality",
    agent=qa_agent
)

#Step 3: Add them to the Crew
crew= Crew(
    agents=[qa_agent],
    tasks=[test_case_task],
    verbose=True,
    cache=False
)

#Step 4: Kick off the agent
def test_qa_agent_output():
    result = crew.kickoff()
    print(result)
    
    # Optional: Add an assertion to tell pytest the test passed if it returned a result
    assert result is not None

if __name__ == "__main__":
    test_qa_agent_output()
