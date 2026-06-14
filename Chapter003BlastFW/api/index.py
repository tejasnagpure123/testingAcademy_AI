import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add parent directory to sys.path so we can import tools
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.jira_connection import fetch_jira_ticket
from tools.test_plan_creator import generate_test_plan

load_dotenv()

app = FastAPI(title="Jira Test Plan Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TestPlanRequest(BaseModel):
    jiraUrl: str = ""
    jiraEmail: str = ""
    jiraToken: str = ""
    issueId: str = "KAN-12"
    groqKey: str = ""

@app.post("/api/generate")
async def generate_plan(request: TestPlanRequest):
    try:
        jira_url = request.jiraUrl or os.getenv("JIRA_URL")
        jira_email = request.jiraEmail or os.getenv("JIRA_EMAIL")
        jira_token = request.jiraToken or os.getenv("JIRA_TOKEN")
        groq_key = request.groqKey or os.getenv("GROQ_KEY")
        issue_id = request.issueId

        if not all([jira_url, jira_email, jira_token, groq_key]):
            raise HTTPException(status_code=400, detail="Missing required configuration. Please provide Jira and Groq credentials.")

        issue_data = fetch_jira_ticket(jira_url, jira_email, jira_token, issue_id)
        test_plan_md = generate_test_plan(groq_key, issue_data)
        
        return {
            "status": "success",
            "issueData": issue_data,
            "testPlanMarkdown": test_plan_md
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
