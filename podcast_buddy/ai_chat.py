import requests

OLLAMA_URL = "http://localhost:11434/api/generate"


def ask_local_ai(question: str) -> str:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "gemma3:4b",
                "prompt": f"""
You are a podcast co-host.
Answer in simple spoken language.
Keep answers under 80 words.
Question:
{question}
""",
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "Sorry, I could not generate an answer.")

    except Exception as exc:
        return f"Error connecting to local AI: {str(exc)}"