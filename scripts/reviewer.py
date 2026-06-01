import os
import json
import httpx
from github import Github

def get_history(issue_number):
    # Логика сбора истории из комментариев GitHub
    pass

def call_groq(messages):
    # Отправка истории в Groq
    pass

def main():
    event = json.loads(os.environ['EVENT_DATA'])
    g = Github(os.environ['GITHUB_TOKEN'])
    
    if 'issue' in event:
        # Это комментарий к PR/Issue
        history = get_history(event['issue']['number'])
        response = call_groq(history)
        # Постинг ответа через g.get_repo(...).get_issue(...).create_comment(...)
    else:
        # Это push - логика старая (diff)
        pass

if __name__ == "__main__":
    main()
