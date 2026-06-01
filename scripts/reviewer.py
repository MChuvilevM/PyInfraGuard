import os
import json
import logging
import httpx
from typing import List, Dict, Any
from github import Github, GithubException, Repository

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ReviewerEngine:
    def __init__(self, token: str, repo_name: str):
        self.github = Github(token)
        self.repo = self.github.get_repo(repo_name)

    def get_pr_diff(self, pr_number: int) -> str:
        """Извлекает diff текущего PR."""
        try:
            pr = self.repo.get_pull(pr_number)
            # Получаем diff через API GitHub
            response = httpx.get(pr.diff_url)
            response.raise_for_status()
            return response.text[:10000]  # Лимит для экономии токенов
        except Exception as e:
            logger.error(f"Failed to fetch PR diff: {e}")
            return ""

    def get_history(self, issue_number: int) -> List[Dict[str, str]]:
        """Собирает историю комментариев."""
        try:
            comments = self.repo.get_issue(number=issue_number).get_comments()
            history = [{"role": "system", "content": "Ты — строгий AI-инженер. Анализируй код, отвечай кратко, исправляй ошибки прямо."}]
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
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"},
                    json={"model": "llama-3.3-70b-versatile", "messages": messages}
                )
                response.raise_for_status()
                return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Groq API Error: {e}")
            raise RuntimeError("AI service unavailable.")

    def run(self, event_data: Dict[str, Any]):
        """Оркестратор логики."""
        # Поддержка как issue_comment, так и pull_request_review_comment
        issue_num = event_data.get('issue', {}).get('number') or event_data.get('pull_request', {}).get('number')
        
        if not issue_num:
            logger.info("No issue/PR number found in event.")
            return

        history = self.get_history(issue_num)
        
        # Добавляем diff, если это PR
        if 'pull_request' in event_data or 'pull_request' in event_data.get('issue', {}).get('pull_request', {}):
            diff = self.get_pr_diff(issue_num)
            if diff:
                history.append({"role": "system", "content": f"Current PR Diff:\n{diff}"})

        reply = self.call_groq(history)
        self.repo.get_issue(number=issue_num).create_comment(reply)
        logger.info("Response posted.")

if __name__ == "__main__":
    engine = ReviewerEngine(os.environ['GITHUB_TOKEN'], os.environ['GITHUB_REPOSITORY'])
    engine.run(json.loads(os.environ['EVENT_DATA']))
