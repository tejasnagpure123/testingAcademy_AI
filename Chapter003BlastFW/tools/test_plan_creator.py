from groq import Groq

def generate_test_plan(groq_key: str, issue_data: dict) -> str:
    """
    Generates a Test Plan using Groq API based on Jira ticket details.
    """
    client = Groq(api_key=groq_key)
    
    prompt = f"""
You are a Senior QA Engineer. Create a comprehensive Test Plan in Markdown format based on the following Jira ticket:

Jira ID: {issue_data.get('id')}
Summary: {issue_data.get('summary')}
Description:
{issue_data.get('description')}

Your Test Plan should include:
1. Overview / Objective
2. Scope (In-Scope and Out-of-Scope)
3. Test Strategy
4. Environment Requirements
5. Test Cases (Positive and Negative scenarios in a table)
6. Deliverables

Format the output entirely in valid Markdown. Do not include introductory text other than the Markdown itself.
    """
    
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a senior QA engineer. You output only valid Markdown.",
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",  # Updated to a supported Groq model
        temperature=0.3,
    )
    
    return chat_completion.choices[0].message.content
