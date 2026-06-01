import os
import json
import logging
from typing import List, Dict, Any, Optional
import httpx
from github import Github, Repository

# Константы
CMD_SUMMARIZE = "/summarize"
CMD_EXPLAIN = "/explain"
DIFF_CHAR_LIMIT = 10000
SYSTEM_PROMPT = "Ты — строгий AI-инженер. Анализируй код, отвечай кратко, исправляй ошибки прямо."

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ReviewerEngine:
    def __init__(self, token: str, repo_name: str) -> None:
        self.github = Github(token)
        self.repo = self.github.get_repo(repo_name)

    def _validate_logger(self) -> None:
        if not all(hasattr(logger, m) for m in ['info', 'warning', 'exception', 'error']):
            raise RuntimeError("Logger configuration invalid.")

    def _handle_request(self, url: str, method: str = "GET", json_data: Optional[Dict] = None) -> Any:
        with httpx.Client(timeout=30.0) as client:
            response = client.request(method, url, json=json_data, headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"})
            response.raise_for_status()
            return response.json()

    def get_pr_diff(self, pr_number: Optional[int]) -> str:
        if not pr_number: return ""
        try:
            pr = self.repo.get_pull(pr_number)
            response = httpx.get(pr.diff_url)
            response.raise_for_status()
            return response.text[:DIFF_CHAR_LIMIT]
        except Exception:
            logger.exception(f"Failed to fetch PR diff for #{pr_number}")
            return ""

    def get_history(self, issue_number: int) -> List[Dict[str, str]]:
        try:
            comments = self.repo.get_issue(number=issue_number).get_comments()
            history = [{"role": "system", "content": SYSTEM_PROMPT}]
            for c in comments:
                role = "assistant" if c.user.type == "Bot" else "user"
                history.append({"role": role, "content": c.body})
            return history
        except Exception:
            logger.exception("Failed to fetch history")
            return []

    def call_groq(self, messages: List[Dict[str, str]]) -> str:
        try:
            data = self._handle_request("https://api.groq.com/openai/v1/chat/completions", "POST", {
                "model": "llama-3.3-70b-versatile", "messages": messages
            })
            return data['choices'][0]['message']['content']
        except Exception:
            logger.exception("Groq API Error")
            return "Ошибка связи с AI-сервисом."

    def handle_command(self, comment_body: str, issue_num: int) -> str:
        if not comment_body: return "Пустой комментарий."
        try:
            parts = comment_body.strip().split()
            command = parts[0] if parts else ""
            if command == CMD_SUMMARIZE: return "Анализирую изменения... [Логика суммаризации]"
            elif command == CMD_EXPLAIN: return "Разбираю логику кода... [Логика объяснения]"
            return f"Неизвестная команда. Доступны: {CMD_SUMMARIZE}, {CMD_EXPLAIN}."
        except Exception as e:
            logger.exception("Error in handle_command")
            return f"Ошибка обработки: {e}"

    def _execute_review(self, issue_num: int) -> str:
        history = self.get_history(issue_num)
        if not history or len(history) <= 1:
            return "История не найдена."
        return self.call_groq(history)

    def run(self, event_data: Dict[str, Any]) -> None:
        self._validate_logger()
        if not isinstance(self.repo, Repository.Repository):
            raise TypeError("Repository not initialized.")
            
        issue_num = (event_data.get('issue', {}).get('number') or event_data.get('pull_request', {}).get('number'))
        if not issue_num:
            logger.error("No valid issue/PR number found.")
            return

        comment = event_data.get('comment')
        comment_body = comment.get('body', '') if isinstance(comment, dict) else ''

        reply = self.handle_command(comment_body, issue_num) if comment_body.startswith('/') else self._execute_review(issue_num)

        try:
            self.repo.get_issue(number=issue_num).create_comment(reply)
            logger.info(f"Response posted to #{issue_num}")
        except Exception:
            logger.exception(f"Failed to post to #{issue_num}")

if __name__ == "__main__":
    try:
        raw_data = os.environ.get('EVENT_DATA', '{}')
        engine = ReviewerEngine(os.environ['GITHUB_TOKEN'], os.environ['GITHUB_REPOSITORY'])
        engine.run(json.loads(raw_data))
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        exit(1)
