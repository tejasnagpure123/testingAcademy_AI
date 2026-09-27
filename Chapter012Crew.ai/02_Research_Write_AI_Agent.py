# QA Research Analyst
# QA Documentation Writer

from crewai import Agent, Task, Crew, Process
from crewai import LLM
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv(Path(__file__).with_name(".env"))

model_name = os.getenv("GROQ_MODEL", "").strip()
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
        f"Missing required settings in .env: {', '.join(missing_settings)}"
    )

model_name = model_name.strip()
if model_name.lower().startswith("openai/openai/"):
    pass
elif model_name.lower().startswith("openai/"):
    model_name = f"openai/{model_name}"
else:
    model_name = f"openai/openai/{model_name}"

groq_llm = LLM(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
)

researcher_agent = Agent(
    role="QA Research Analyst",
    goal="Find the common bugs in web application",
    backstory="You are a QA researcher who has analyzed thousands of bug reports  across web applications. You specialize in identifying the patterns and trend in the software defects",
    llm=groq_llm,
    verbose=True,
)

writer_agent = Agent(
    role="QA Documentation Writer",
    goal="Create clear , actionable bug preventation guidelines",
    backstory="YOu are a technical writer specializing in QA documentation. You turn complex bug data into simple actionalble checklists that developers can follow",
    llm=groq_llm,
    verbose=True,
)

research_Task = Task(
    description="Research and list the top 5 most common bug categories in modern web applications.  For each category provide name, frequency(percentage) example and impact levels",
    expected_output=" A ranked list of 5 bugs categories with name, frequency , exampke and impact for each ",
    agent=researcher_agent,
)
writing_Task = Task(
    description="Based on the research provided , create a 'Bug Prevention Checklist' that developers can use before submitting a pull request. Make it practical and actionable. ",
    expected_output="A formatter checklist with 5-10 items that developers can quickly review before code simulation.",
    agent=writer_agent,
)

crew = Crew(
    agents=[researcher_agent, writer_agent],
    tasks=[research_Task, writing_Task],
    process=Process.sequential,
    verbose=True,
)


result = crew.kickoff()
print(result)
