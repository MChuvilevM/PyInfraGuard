import os
import sys
import json
import httpx
from github import Github, GithubException

def get_env(var_name):
    val = os.getenv(var_name)
    if not val:
        print(f"Error: Environment variable {var_name} not set")
        sys.exit(1)
    return val

def get_history(repo, issue_number):
    try:
        comments = repo.get_issue(number=issue_number).get_comments()
        history = [{"role": "system", "content": "Ты — строгий AI-инженер. Анализируй код, отвечай кратко, исправляй ошибки прямо."}]
        for c in comments:
            role = "assistant" if c.user.type == "Bot" else "user"
            history.append({"role": role, "content": c.body})
        return history
    except GithubException as e:
        print(f"Error fetching history: {e}")
        return []

def call_groq(messages):
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {get_env('GROQ_API_KEY')}"},
                json={"model": "llama-3.3-70b-versatile", "messages": messages}
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"Groq API Error: {e}")
        return "Ошибка обработки запроса к AI."

def main():
    event_data = get_env('EVENT_DATA')
    event = json.loads(event_data)
    
    g = Github(get_env('GITHUB_TOKEN'))
    repo = g.get_repo(get_env('GITHUB_REPOSITORY'))
    
    if 'issue' in event:
        issue_num = event['issue'].get('number')
        if not issue_num:
            print("Error: No issue number in event")
            return
            
        history = get_history(repo, issue_num)
        if history:
            reply = call_groq(history)
            repo.get_issue(number=issue_num).create_comment(reply)
    else:
        print("Not an issue comment event.")

if __name__ == "__main__":
    main()
