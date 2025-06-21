import os

class AdvancedConfig:
    LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")
    LLAMA_API_URL = os.getenv("LLAMA_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    LLAMA_MODEL_NAME = os.getenv("LLAMA_MODEL_NAME", "llama-3-70b-8192")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    CLAUDE_MODEL_NAME = os.getenv("CLAUDE_MODEL_NAME", "claude-3-opus-20240229")
    MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "llama")  # or "claude"
    # ...rest of your config as before