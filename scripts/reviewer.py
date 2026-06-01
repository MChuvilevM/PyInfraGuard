import os
import sys
import logging
import json
from typing import List, Dict, Any
import httpx
from github import Github, GithubException, Repository, Issue

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def get_env(var_name: str) -> str:
    """Получает переменную окружения или вызывает исключение при её отсутствии."""
    val = os.environ.get(var_name)
    if not val:
        raise EnvironmentError(f"Missing required environment variable: {var_name}")
    return val

def get_history(repo: Repository, issue_number: int) -> List[Dict[str, str]]:
    """Собирает историю комментариев для поддержания контекста диалога."""
    try:
        comments = repo.get_issue(number=issue_number).get_comments()
        history = [{"role": "system", "content": "Ты — строгий AI-инженер. Анализируй код, отвечай кратко, исправляй ошибки прямо."}]
        for c in comments:
            role = "assistant" if c.user.type == "Bot" else "user"
            history.append({"role": role, "content": c.body})
        return history
    except GithubException as e:
        logger.error(f"Failed to fetch history: {e}")
        raise

def call_groq(messages: List[Dict[str, str]]) -> str:
    """Отправляет контекст диалога в Groq API для генерации ответа."""
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
        logger.error(f"Groq API Error: {e}")
        raise RuntimeError("AI service is currently unavailable.")

def main() -> None:
    """Основная точка входа для обработки событий GitHub."""
    try:
        event = json.loads(get_env('EVENT_DATA'))
        g = Github(get_env('GITHUB_TOKEN'))
        repo = g.get_repo(get_env('GITHUB_REPOSITORY'))
        
        if 'issue' in event:
            issue_num = event['issue'].get('number')
            history = get_history(repo, issue_num)
            reply = call_groq(history)
            repo.get_issue(number=issue_num).create_comment(reply)
            logger.info("Response successfully posted.")
        else:
            logger.info("Not an issue comment event, skipping.")
            
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
