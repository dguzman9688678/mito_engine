import os
import requests

try:
    from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
except ImportError:
    Anthropic = None
    HUMAN_PROMPT = "\n\nHuman:"
    AI_PROMPT = "\n\nAssistant:"

def llama3_generate(prompt: str) -> str:
    url = os.getenv("LLAMA_API_URL")
    api_key = os.getenv("LLAMA_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": os.getenv("LLAMA_MODEL_NAME"),
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
        "temperature": 0.7
    }
    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def claude_generate(prompt: str) -> str:
    if Anthropic is None:
        raise ImportError("anthropic package not installed")
    client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
    completion = client.completions.create(
        model=os.getenv("CLAUDE_MODEL_NAME"),
        max_tokens_to_sample=1024,
        prompt=f"{HUMAN_PROMPT} {prompt}{AI_PROMPT}"
    )
    return completion.completion

def ai_generate(prompt: str) -> str:
    provider = os.getenv("MODEL_PROVIDER", "llama")
    if provider == "claude":
        return claude_generate(prompt)
    else:
        return llama3_generate(prompt)