import os
import httpx

def _handle_request(self, messages):
    # Берем новый секрет
    api_key = os.environ.get('API_GEMINI')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    # Конвертация формата OpenAI в формат Gemini
    payload = {
        "contents": [{"parts": [{"text": m["content"]}]} for m in messages]
    }
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Извлекаем текст ответа из структуры Gemini
        return data["candidates"][0]["content"]["parts"][0]["text"]
