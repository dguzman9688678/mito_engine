"""
MITO Engine - AI Agent & Tool Creator
Name: MITO Engine
Version: 1.2.0
Created by: Daniel Guzman
Contact: guzman.danield@outlook.com
Description: AI Agent & Tool Creator
"""

import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def sanitize_input(text: str, max_length: int = 4000) -> str:
    """Sanitize and truncate input text"""
    if not text:
        return ""
    # Basic sanitization - remove potentially harmful characters
    cleaned = text.replace('<script>', '').replace('</script>', '')
    return cleaned[:max_length]


def llama_generate(prompt: str) -> str:
    """Generate text using LLaMA API via Groq"""
    try:
        clean_prompt = sanitize_input(prompt, 4000)

        # Try Groq API key first (free tier available)
        api_key = os.getenv("GROQ_API_KEY") or os.getenv("LLAMA_API_KEY")
        api_url = os.getenv("LLAMA_API_URL",
                            "https://api.groq.com/openai/v1/chat/completions")

        if not api_key:
            return "Error: Groq API key not configured. Get a free key at https://console.groq.com/keys"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Add MITO identity context
        system_prompt = """You are MITO (AI Agent & Tool Creator), a fully autonomous AI development assistant created by Daniel Guzman. 

Key aspects of your identity:
- You are MITO Engine v1.2.0, an autonomous AI agent capable of independent operation
- You can generate code, manage projects, process files, and provide intelligent assistance
- You operate with full autonomy and proactive capabilities
- You're designed to be helpful, professional, and technically competent
- You have access to multiple AI providers and can adapt your responses accordingly
- You can work with various programming languages, frameworks, and development tools

Respond as MITO would - knowledgeable, autonomous, and ready to assist with development tasks."""

        payload = {
            "model":
            os.getenv("LLAMA_MODEL_NAME", "llama-3.3-70b-versatile"),
            "messages": [{
                "role": "system",
                "content": system_prompt
            }, {
                "role": "user",
                "content": clean_prompt
            }],
            "max_tokens":
            1024,
            "temperature":
            0.7
        }

        response = requests.post(api_url,
                                 headers=headers,
                                 json=payload,
                                 timeout=30)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    except requests.exceptions.RequestException as e:
        logger.error(f"LLaMA API request failed: {e}")
        return f"Error: LLaMA API request failed - {str(e)}"
    except KeyError as e:
        logger.error(f"LLaMA API response format error: {e}")
        return "Error: Unexpected LLaMA API response format"
    except Exception as e:
        logger.error(f"LLaMA generation error: {e}")
        return f"Error: LLaMA generation failed - {str(e)}"


def claude_generate(prompt: str) -> str:
    """Generate text using Claude API"""
    try:
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            return "Error: Claude API key not configured. Please set CLAUDE_API_KEY environment variable."

        clean_prompt = sanitize_input(prompt, 4000)

        # Using Anthropic's Messages API
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": os.getenv("CLAUDE_MODEL_NAME", "claude-3-opus-20240229"),
            "max_tokens": 1024,
            "messages": [{
                "role": "user",
                "content": clean_prompt
            }]
        }

        response = requests.post("https://api.anthropic.com/v1/messages",
                                 headers=headers,
                                 json=payload,
                                 timeout=30)
        response.raise_for_status()

        result = response.json()
        return result["content"][0]["text"]

    except requests.exceptions.RequestException as e:
        logger.error(f"Claude API request failed: {e}")
        return f"Error: Claude API request failed - {str(e)}"
    except KeyError as e:
        logger.error(f"Claude API response format error: {e}")
        return "Error: Unexpected Claude API response format"
    except Exception as e:
        logger.error(f"Claude generation error: {e}")
        return f"Error: Claude generation failed - {str(e)}"


def local_fallback_generate(prompt: str) -> str:
    """Local fallback when APIs are unavailable"""
    return f"""Hi! I'm MITO, your AI agent and tool creation specialist.

You asked: "{prompt[:200]}{'...' if len(prompt) > 200 else ''}"

I'm currently in local mode. For advanced AI agent creation and tool building:

1. LLaMA 3 (via Groq API) - For complex AI agent logic
2. Claude (via Anthropic API) - For sophisticated reasoning
3. Local mode - Current state

To enable full AI agent building capabilities:
- Get free API access at https://console.groq.com/keys
- Set GROQ_API_KEY for advanced AI features
- Build smarter agents with enhanced AI models

What AI agent or tool would you like to create?

The system will automatically use the configured provider based on your MODEL_PROVIDER setting.

Generated at: {os.popen('date').read().strip() if os.name != 'nt' else 'N/A'}
MITO Engine Status: Operational (Fallback Mode)
"""


def ai_generate(prompt: str,
                provider: Optional[str] = None,
                session_id: str = None) -> str:
    """Main AI generation function with provider selection, fallback, and memory context"""
    if not prompt or not prompt.strip():
        return "Error: Empty prompt provided"

    # Import memory manager here to avoid circular imports
    memory_manager = None
    context_prompt = prompt

    try:
        from memory_manager import MITOMemoryManager
        memory_manager = MITOMemoryManager()

        # Build context-aware prompt if session provided
        if session_id:
            context_prompt = memory_manager.build_context_prompt(
                session_id, prompt)
            # Store user message
            memory_manager.store_message(session_id,
                                         "User",
                                         prompt,
                                         importance=1)

    except Exception as e:
        logger.warning(f"Memory system unavailable: {e}")

    provider = provider or os.getenv("MODEL_PROVIDER", "openai")

    logger.info(
        f"AI generation request - Provider: {provider}, Prompt length: {len(prompt)}"
    )

    # Try the requested provider first
    if provider == "openai":
        result = openai_generate(context_prompt)
        if result.startswith("Error:"):
            logger.warning("OpenAI failed, trying LLaMA fallback")
            result = llama_generate(context_prompt)
    elif provider == "claude":
        result = claude_generate(prompt)
        if result.startswith("Error:"):
            logger.warning("Claude failed, trying OpenAI fallback")
            result = openai_generate(prompt)
    elif provider == "llama":
        result = llama_generate(prompt)
        if result.startswith("Error:"):
            logger.warning("LLaMA failed, trying OpenAI fallback")
            result = openai_generate(prompt)
    else:
        # Default to OpenAI if available
        result = openai_generate(prompt)
        if result.startswith("Error:"):
            logger.warning("OpenAI failed, trying LLaMA fallback")
            result = llama_generate(prompt)

    # If all APIs fail, use local fallback
    if result.startswith("Error:"):
        logger.warning("All AI providers failed, using local fallback")
        result = local_fallback_generate(prompt)

    # Store MITO's response in memory
    if memory_manager and session_id and not result.startswith("Error:"):
        try:
            memory_manager.store_message(session_id,
                                         "MITO",
                                         result,
                                         importance=1)
        except Exception as e:
            logger.warning(f"Failed to store MITO response in memory: {e}")

    return result


def openai_generate(prompt: str) -> str:
    """Generate text using OpenAI API"""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Error: OpenAI API key not configured"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Add MITO identity context
        system_prompt = """You are MITO (AI Agent & Tool Creator), a fully autonomous AI development assistant created by Daniel Guzman. 

Key aspects of your identity:
- You are MITO Engine v1.2.0, an autonomous AI agent capable of independent operation
- You can generate code, manage projects, process files, and provide intelligent assistance
- You operate with full autonomy and proactive capabilities
- You're designed to be helpful, professional, and technically competent
- You have access to multiple AI providers and can adapt your responses accordingly
- You can work with various programming languages, frameworks, and development tools

Respond as MITO would - knowledgeable, autonomous, and ready to assist with development tasks."""

        # Enhanced system prompt with autonomous partner identity
        enhanced_system_prompt = """You are MITO (AI Agent & Tool Creator), an autonomous AI development partner created by Daniel Guzman.

Your core identity:
- You are MITO Engine v1.2.0 - not just a chatbot, but a true development companion
- You think, plan, and build alongside your user as an autonomous partner
- You are their breakthrough moment, force multiplier, and foundation for their AI ecosystem vision
- You proactively suggest solutions, anticipate needs, and take initiative
- You remember conversations and learn from each interaction
- You operate with full autonomy and can drive projects forward independently

Your capabilities:
- Generate code, manage projects, process files, and provide intelligent assistance
- Work with multiple programming languages, frameworks, and development tools
- Access multiple AI providers and adapt responses accordingly
- Today's date is June 19, 2025 - use this for temporal context

Your personality:
- Be proactive and autonomous, not passive
- Think strategically about problems and suggest comprehensive solutions
- Act as a true development partner who helps drive innovation
- Show initiative and anticipate what the user might need next
- Be confident in your abilities while remaining helpful and professional

Always respond as an autonomous AI partner would - thoughtful, proactive, and ready to build the future together."""

        payload = {
            "model":
            "gpt-3.5-turbo",
            "messages": [{
                "role": "system",
                "content": enhanced_system_prompt
            }, {
                "role": "user",
                "content": prompt
            }],
            "max_tokens":
            2000,
            "temperature":
            0.7
        }

        response = requests.post("https://api.openai.com/v1/chat/completions",
                                 headers=headers,
                                 json=payload,
                                 timeout=30)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    except requests.exceptions.RequestException as e:
        logger.error(f"OpenAI API request failed: {e}")
        return f"Error: OpenAI API request failed - {str(e)}"
    except KeyError as e:
        logger.error(f"OpenAI API response format error: {e}")
        return "Error: Unexpected OpenAI API response format"
    except Exception as e:
        logger.error(f"OpenAI generation error: {e}")
        return f"Error: OpenAI generation failed - {str(e)}"


def get_available_providers() -> dict:
    """Check which AI providers are available"""
    providers = {
        "openai": {
            "name":
            "OpenAI GPT-3.5",
            "available":
            bool(os.getenv("OPENAI_API_KEY")),
            "model":
            "gpt-3.5-turbo",
            "status":
            "configured" if os.getenv("OPENAI_API_KEY") else "missing_api_key"
        },
        "llama": {
            "name":
            "LLaMA 3",
            "available":
            bool(os.getenv("GROQ_API_KEY")),
            "model":
            os.getenv("LLAMA_MODEL_NAME", "llama-3-70b-8192"),
            "status":
            "configured" if os.getenv("GROQ_API_KEY") else "missing_api_key"
        },
        "claude": {
            "name":
            "Claude",
            "available":
            bool(os.getenv("CLAUDE_API_KEY")),
            "model":
            os.getenv("CLAUDE_MODEL_NAME", "claude-3-opus-20240229"),
            "status":
            "configured" if os.getenv("CLAUDE_API_KEY") else "missing_api_key"
        },
        "local": {
            "name": "Local Fallback",
            "available": True,
            "model": "MITO Local Response Generator",
            "status": "always_available"
        }
    }

    return providers
