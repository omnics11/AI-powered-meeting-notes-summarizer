import os
import requests

class AIClient:
    def __init__(self, model: str | None = None):
        self.model = model or "llama3-8b-8192"
        self.api_key = os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    def summarize(self, instruction: str, transcript: str) -> str:
        system_prompt = (
            "You are an assistant that produces clean, structured meeting summaries.\n"
            "Return concise bullets, decisions, owners, and deadlines. "
            "Keep action items clearly marked."
        )
        user_prompt = (
            f"Instruction: {instruction}\n\n"
            f"Transcript:\n{transcript}\n\n"
            f"Return a structured summary with sections: Overview, Key Points, Decisions, Action Items, Risks."
        )

        headers = {"Authorization": f"Bearer {self.api_key}"}
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        resp = requests.post(self.base_url, headers=headers, json=data)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
