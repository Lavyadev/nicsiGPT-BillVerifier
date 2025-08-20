import requests
import logging
import os
MODEL_DEFAULT = os.getenv("OLLAMA_MODEL", "llama3:8b")
TIMEOUT_S = int(os.getenv("OLLAMA_TIMEOUT", "180"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
def call_llm_with_prompt(prompt: str, model: str = MODEL_DEFAULT) -> str:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=TIMEOUT_S
        )
        response.raise_for_status()
        data = response.json()
        return (data.get("response") or "").strip()
    except Exception as e:
        logging.error(f"Ollama LLM call failed: {e}")
        return ""