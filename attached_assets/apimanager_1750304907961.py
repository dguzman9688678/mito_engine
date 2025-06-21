import os
import requests

try:
    from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
except ImportError:
    Anthropic = None
    HUMAN_PROMPT = "\n\nHuman:"
    AI_PROMPT = "\n\nAssistant:"

def free_llm_generate(prompt: str, model: str = None) -> str:
    """
    Example: Use HuggingFace Inference API or any public LLM provider.
    Customize this for your preferred free LLM API.
    """
    api_url = os.getenv("FREE_LLM_API_URL", "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct")
    api_key = os.getenv("FREE_LLM_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}" if api_key else "",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 512}
    }
    resp = requests.post(api_url, headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()
    # HuggingFace returns a list of dicts with 'generated_text'
    if isinstance(data, list) and "generated_text" in data[0]:
        return data[0]["generated_text"]
    # Some APIs just return "generated_text"
    if "generated_text" in data:
        return data["generated_text"]
    # fallback: return the whole response as string
    return str(data)

def claude_generate(prompt: str) -> str:
    """Call Anthropic Claude API (Claude 3)."""
    if Anthropic is None:
        raise ImportError("anthropic package not installed")
    client = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
    completion = client.completions.create(
        model=os.getenv("CLAUDE_MODEL_NAME", "claude-3-opus-20240229"),
        max_tokens_to_sample=1024,
        prompt=f"{HUMAN_PROMPT} {prompt}{AI_PROMPT}"
    )
    return completion.completion

def generate(prompt: str, provider: str = None) -> str:
    """
    Unified interface: provider can be 'free' (default), 'claude', or others you add.
    """
    provider = provider or os.getenv("MODEL_PROVIDER", "free")
    if provider == "claude":
        return claude_generate(prompt)
    # Add more providers as elif cases if needed
    else:
        return free_llm_generate(prompt)

# Optionally, expose available providers for use in UI/API
AVAILABLE_PROVIDERS = ["free", "claude"]