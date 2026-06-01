import os
import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from github import Github, GithubException, Repository

# Константы
DIFF_CHAR_LIMIT = 10000
SYSTEM_PROMPT = "Ты — строгий AI-инженер. Анализируй код, отвечай кратко, исправляй ошибки прямо."

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ReviewerEngine:
    """Движок для интерактивного код-ревью в GitHub через LLM."""
    
    def __init__(self, token: str, repo_name: str) -> None:
        self.github = Github(token)
        self.repo = self.github.get_repo(repo_name)

    def _handle_request(self, url: str, method: str = "GET", json_data: Optional[Dict] = None) -> Any:
        """Вспомогательный метод для унификации сетевых запросов."""
        with httpx.Client(timeout=30.0) as client:
            response = client.request(method, url, json=json_data, headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"})
            response.raise_for_status()
            return response.json()

    def get_pr_diff(self, pr_number: Optional[int]) -> str:
        """Извлекает diff текущего PR."""
        if not pr_number:
            return ""
        try:
            pr = self.repo.get_pull(pr_number)
            response = httpx.get(pr.diff_url)
            response.raise_for_status()
            return response.text[:DIFF_CHAR_LIMIT]
        except Exception as e:
            logger.error(f"Failed to fetch PR diff: {e}")
            return ""

    def get_history(self, issue_number: int) -> List[Dict[str, str]]:
        """Собирает историю комментариев для контекста."""
        try:
            comments = self.repo.get_issue(number=issue_number).get_comments()
            history = [{"role": "system", "content": SYSTEM_PROMPT}]
            for c in comments:
                role = "assistant" if c.user.type == "Bot" else "user"
                history.append({"role": role, "content": c.body})
            return history
        except GithubException as e:
            logger.error(f"Failed to fetch history: {e}")
            raise

    def call_groq(self, messages: List[Dict[str, str]]) -> str:
        """Взаимодействие с Groq API."""
        try:
            data = self._handle_request("https://api.groq.com/openai/v1/chat/completions", "POST", {
                "model": "llama-3.3-70b-versatile", "messages": messages
            })
            return data['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Groq API Error: {e}")
            raise RuntimeError("AI service unavailable.")

    def run(self, event_data: Dict[str, Any]):
        # Логируем, что именно пришло
        logger.info(f"Event received. Keys: {list(event_data.keys())}")
        
        # Защита от ответов самому себе
        if event_data.get('sender', {}).get('login') == 'github-actions[bot]':
            logger.info("Ignoring own activity.")
            return

        # Пытаемся найти номер issue/PR независимо от структуры события
        issue_num = (event_data.get('issue', {}).get('number') or 
                     event_data.get('pull_request', {}).get('number'))
        
        if not issue_num:
            logger.warning("No issue/PR number found. Aborting.")
            return

        logger.info(f"Processing issue #{issue_num}")
        
        history = self.get_history(issue_num)
        
        # Если это PR, добавляем diff в контекст
        if 'pull_request' in event_data or event_data.get('issue', {}).get('pull_request'):
            diff = self.get_pr_diff(issue_num)
            if diff:
                history.append({"role": "system", "content": f"Current PR Diff:\n{diff}"})

        reply = self.call_groq(history)
        self.repo.get_issue(number=issue_num).create_comment(reply)
        logger.info("Response posted.")

if __name__ == "__main__":
    try:
        raw_data = os.environ.get('EVENT_DATA', '{}')
        data = json.loads(raw_data)
        engine = ReviewerEngine(os.environ['GITHUB_TOKEN'], os.environ['GITHUB_REPOSITORY'])
        engine.run(data)
    except json.JSONDecodeError as e:
        logger.critical(f"Invalid JSON in EVENT_DATA: {e}")
        exit(1)
