import json
import re
import time
import requests

class GeminiError(RuntimeError):
    pass

class GeminiClient:
    def __init__(self, api_key, model):
        if not api_key:
            raise GeminiError("Missing GEMINI_API_KEY. Add it as a GitHub Actions secret.")
        self.api_key = api_key
        self.model = model

    def generate(self, system_prompt, user_text, temperature=0.85, retries=3):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_text}]}],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json"
            }
        }
        for attempt in range(retries):
            response = requests.post(
                url, params={"key": self.api_key}, json=payload, timeout=90
            )
            if response.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            if not response.ok:
                raise GeminiError(f"Gemini API {response.status_code}: {response.text[:900]}")
            data = response.json()
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return _extract_json(text)
            except (KeyError, IndexError, TypeError) as exc:
                raise GeminiError(f"Gemini returned an unexpected response: {data}") from exc
        raise GeminiError("Gemini request failed after retries.")

def _extract_json(text):
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise GeminiError(f"Could not parse Gemini JSON: {cleaned[:500]}") from exc
