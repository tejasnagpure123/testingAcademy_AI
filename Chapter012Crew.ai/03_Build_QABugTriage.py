# Define Your QA Team
# # Our task of BugTriageCrew is to prioritize, analyze, find RCA (root cause analysis)
# for these applications.
# In short -> Why bug occurs?

# Daily - MT - 30min for 30 people( target 10-20 Bugs)
# Man hours per month -> 30*30*20 -> 18000/60 ->
# Waste ->  30 hour man , 300$ -> ~ $10000, ~5-10Lac ->

# Define Your QA Team
# # Our task of BugTriageCrew is to prioritize, analyze, find RCA (root cause analysis)
# for these applications.
# In short -> Why bug occurs?

# # Sample bug report
# bug_report = """
# Bug Title: Shopping cart total shows $0.00 after applying discount code
# Bug ID: BUG-4521
# Reporter: manual_tester_jane
# Environment: Production, Chrome 120, Windows 11
# Severity (Reporter): High

# Steps to Reproduce:
# 1. Add 3+ items to shopping cart (total > $50)
# 2. Apply discount code "SAVE20" (20% off)
# 3. Observe the cart total

# Actual Result: Cart total shows $0.00 instead of discounted price
# Expected Result: Cart total should show original price minus 20%

# Additional Info:
# - Happens only when cart has 3+ items
# - Works fine with 1-2 items
# - Started after last Friday's deployment (v2.4.1)
# - No errors in browser console
# - API response shows correct discounted amount
# """

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

"""QA Bug Triage Agents — Each agent is a specialist."""

# 5*30  people who can rweview the CREW AI - Yes

# Agent 1: Bug Triage Analyst
# Agent 2: Root Cause Investigator
# Agent 3: Test Recommendation Agent

# Task 1: Classify the bug
# Task 2: Investigate root cause (uses triage output as context)
# Task 3: Recommend tests (uses both previous outputs)
