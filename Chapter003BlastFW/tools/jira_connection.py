import requests
from requests.auth import HTTPBasicAuth

def fetch_jira_ticket(base_url: str, email: str, token: str, issue_id: str) -> dict:
    """
    Fetches a Jira ticket's summary and description using the Jira REST API v2.
    """
    url = f"{base_url.rstrip('/')}/rest/api/2/issue/{issue_id}"
    auth = HTTPBasicAuth(email, token)
    headers = {"Accept": "application/json"}
    
    response = requests.get(url, headers=headers, auth=auth)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch Jira ticket {issue_id}. Status Code: {response.status_code}. Response: {response.text}")
    
    data = response.json()
    fields = data.get("fields", {})
    
    return {
        "id": issue_id,
        "summary": fields.get("summary", "No Summary"),
        "description": fields.get("description", "No Description")
    }
