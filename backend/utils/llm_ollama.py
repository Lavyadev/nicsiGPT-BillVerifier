import requests
import logging

def call_llm_with_prompt(prompt: str, model: str = "llama3:8b") -> str:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=180
        )
        return response.json().get("response", "").strip()
    except Exception as e:
        logging.error(f"🔥 Ollama LLM call failed: {e}")
        return ""
