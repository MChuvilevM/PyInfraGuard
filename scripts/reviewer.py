import os
import json
import logging
import httpx
from typing import List, Dict, Any, Optional

# Константы
DIFF_CHAR_LIMIT = 10000
SYSTEM_PROMPT = "Ты — строгий AI-инженер. Анализируй код, отвечай кратко, исправляй ошибки прямо."

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class ReviewerEngine:
    """Движок для интерактивного код-ревью в GitHub через LLM."""
    
    def __init__(self, token: str, repo_name: str) -> None:
        from github import Github
        self.github = Github(token)
        self.repo = self.github.get_repo(repo_name)

    def _validate_logger(self) -> None:
        """Проверка наличия методов логирования."""
        if not all(hasattr(logger, method) for method in ['info', 'warning', 'exception']):
            raise RuntimeError("Logger is not properly configured.")

    def _handle_request(self, url: str, method: str = "GET", json_data: Optional[Dict] = None) -> Any:
        with httpx.Client(timeout=30.0) as client:
            response = client.request(method, url, json=json_data, headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"})
            response.raise_for_status()
            return response.json()

    def get_pr_diff(self, pr_number: Optional[int]) -> str:
        if not pr_number:
            return ""
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
            raise

    def call_groq(self, messages: List[Dict[str, str]]) -> str:
        try:
            data = self._handle_request("https://api.groq.com/openai/v1/chat/completions", "POST", {
                "model": "llama-3.3-70b-versatile", "messages": messages
            })
            return data['choices'][0]['message']['content']
        except Exception:
            logger.exception("Groq API Error")
            raise RuntimeError("AI service unavailable.")

    def run(self, event_data: Dict[str, Any]) -> None:
        self._validate_logger()
        logger.info(f"Event received. Keys: {list(event_data.keys())}")
        
        if event_data.get('sender', {}).get('login') == 'github-actions[bot]':
            logger.info("Ignoring own activity.")
            return

        issue_num = (event_data.get('issue', {}).get('number') or 
                     event_data.get('pull_request', {}).get('number'))
        
        if not issue_num:
            raise ValueError("No issue/PR number found in event data.")

        logger.info(f"Processing issue #{issue_num}")
        
        history = self.get_history(issue_num)
        
        if 'pull_request' in event_data or event_data.get('issue', {}).get('pull_request'):
            diff = self.get_pr_diff(issue_num)
            if diff:
                history.append({"role": "system", "content": f"Current PR Diff:\n{diff}"})

        reply = self.call_groq(history)
        self.repo.get_issue(number=issue_num).create_comment(reply)
        logger.info(f"Response successfully posted to issue #{issue_num}")

if __name__ == "__main__":
    try:
        raw_data = os.environ.get('EVENT_DATA', '{}')
        data = json.loads(raw_data)
        engine = ReviewerEngine(os.environ['GITHUB_TOKEN'], os.environ['GITHUB_REPOSITORY'])
        engine.run(data)
    except json.JSONDecodeError:
        logger.exception("Invalid JSON in EVENT_DATA")
        exit(1)
    except Exception as e:
        logger.exception(f"Critical execution error: {e}")
        exit(1)
