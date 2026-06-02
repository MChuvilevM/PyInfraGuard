import os
import httpx
import sys

def _handle_request(self, messages: list) -> str:
    api_key = os.environ.get('API_GEMINI')
    
    if not api_key:
        print("ERROR: API_GEMINI environment variable is not set")
        sys.exit(1)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": m["content"]}]} for m in messages]
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"ERROR: Request failed: {e}")
        sys.exit(1)
