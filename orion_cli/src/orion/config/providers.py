"""Provider abstraction layer for LLM backends."""

from enum import Enum
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel
else:
    BaseChatModel = Any


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    LMSTUDIO = "lmstudio"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


def get_llm(settings: Any) -> BaseChatModel:
    """
    Factory function to instantiate the appropriate LLM based on provider settings.
    
    Supports thinking_mode (off/low/medium/high) for reasoning models.
    When thinking_mode is active, reasoning parameters are passed to the LLM.
    
    Args:
        settings: Settings object with get() method
        
    Returns:
        BaseChatModel instance (ChatOllama, ChatOpenAI, or ChatAnthropic)
        
    Raises:
        ValueError: If provider is not supported or required dependencies are missing
    """
    provider = settings.get("llm_provider", "ollama")
    thinking_mode = settings.get("thinking_mode", "off")
    
    if provider == LLMProvider.OLLAMA:
        return _get_ollama_llm(settings, thinking_mode)
    elif provider == LLMProvider.LMSTUDIO:
        return _get_lmstudio_llm(settings, thinking_mode)
    elif provider == LLMProvider.OPENAI:
        return _get_openai_llm(settings, thinking_mode)
    elif provider == LLMProvider.ANTHROPIC:
        return _get_anthropic_llm(settings, thinking_mode)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def _get_ollama_llm(settings: Any, thinking_mode: str = "off") -> BaseChatModel:
    """Create ChatOllama instance."""
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        raise ImportError(
            "langchain-ollama package not installed. "
            "Install it with: pip install langchain-ollama"
        )
    
    kwargs = dict(
        model=settings.get("model", "qwen2.5-coder:14b"),
        temperature=float(settings.get("model_temperature", 0.7)),
        num_ctx=int(settings.get("model_context_length", 8192)),
    )
    
    # Ollama: thinking models use num_predict for reasoning budget
    if thinking_mode != "off":
        thinking_budget = {"low": 1024, "medium": 4096, "high": 16384}.get(thinking_mode, 4096)
        kwargs["num_predict"] = thinking_budget
    
    return ChatOllama(**kwargs)


def _get_lmstudio_llm(settings: Any, thinking_mode: str = "off") -> BaseChatModel:
    """Create ChatOpenAI instance configured for LM Studio."""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai package not installed. "
            "Install it with: pip install langchain-openai"
        )
    
    base_url = settings.get("lmstudio_base_url", "http://localhost:1234/v1")
    api_key = settings.get("lmstudio_api_key", "lm-studio")
    model = settings.get("model", "local-model")
    
    kwargs = dict(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=float(settings.get("model_temperature", 0.7)),
        max_tokens=int(settings.get("model_context_length", 8192)),
    )
    
    # LM Studio: pass reasoning_effort if supported
    if thinking_mode != "off":
        kwargs["model_kwargs"] = {"reasoning_effort": thinking_mode}
    
    return ChatOpenAI(**kwargs)


def _get_openai_llm(settings: Any, thinking_mode: str = "off") -> BaseChatModel:
    """Create ChatOpenAI instance for OpenAI API."""
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai package not installed. "
            "Install it with: pip install langchain-openai"
        )
    
    api_key = settings.get("openai_api_key")
    if not api_key:
        raise ValueError(
            "OpenAI API key required. Set it with: /settings set openai_api_key YOUR_KEY"
        )
    
    model = settings.get("model", "gpt-4o")
    
    # OpenAI: use reasoning models when thinking is on
    if thinking_mode != "off":
        reasoning_models = {"low": "o3-mini", "medium": "o3-mini", "high": "o3"}
        model = reasoning_models.get(thinking_mode, "o3-mini")
    
    kwargs = dict(
        api_key=api_key,
        model=model,
        temperature=float(settings.get("model_temperature", 0.7)),
        max_tokens=int(settings.get("model_context_length", 8192)),
    )
    
    # OpenAI reasoning models use reasoning_effort parameter
    if thinking_mode != "off":
        kwargs["model_kwargs"] = {"reasoning_effort": thinking_mode}
    
    return ChatOpenAI(**kwargs)


def _get_anthropic_llm(settings: Any, thinking_mode: str = "off") -> BaseChatModel:
    """Create ChatAnthropic instance for Anthropic/Claude API."""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError(
            "langchain-anthropic package not installed. "
            "Install it with: pip install langchain-anthropic"
        )
    
    api_key = settings.get("anthropic_api_key")
    if not api_key:
        raise ValueError(
            "Anthropic API key required. Set it with: /settings set anthropic_api_key YOUR_KEY"
        )
    
    model = settings.get("model", "claude-3-5-sonnet-20241022")
    
    kwargs = dict(
        api_key=api_key,
        model=model,
        temperature=float(settings.get("model_temperature", 0.7)),
        max_tokens=int(settings.get("model_context_length", 8192)),
    )
    
    # Anthropic: enable extended thinking when mode is on
    if thinking_mode != "off":
        thinking_budget = {"low": 4096, "medium": 16384, "high": 32768}.get(thinking_mode, 16384)
        kwargs["model_kwargs"] = {
            "thinking": {
                "type": "enabled",
                "budget_tokens": thinking_budget,
            }
        }
    
    return ChatAnthropic(**kwargs)


def list_available_models(settings: Any) -> list[str]:
    """
    List available models for the configured provider.
    
    Args:
        settings: Settings object with get() method
        
    Returns:
        List of available model names
    """
    provider = settings.get("llm_provider", "ollama")
    
    if provider == LLMProvider.OLLAMA:
        return _list_ollama_models()
    elif provider == LLMProvider.LMSTUDIO:
        return _list_lmstudio_models(settings)
    elif provider == LLMProvider.OPENAI:
        return _list_openai_models()
    elif provider == LLMProvider.ANTHROPIC:
        return _list_anthropic_models()
    else:
        return []


def _list_ollama_models() -> list[str]:
    """List available Ollama models."""
    try:
        import ollama
        return [m.model for m in ollama.list().models]
    except Exception:
        return []


def _list_lmstudio_models(settings: Any) -> list[str]:
    """List available LM Studio models via OpenAI-compatible API."""
    try:
        import httpx
        base_url = settings.get("lmstudio_base_url", "http://localhost:1234/v1")
        api_key = settings.get("lmstudio_api_key", "lm-studio")
        
        response = httpx.get(
            f"{base_url}/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()
        return [model["id"] for model in data.get("data", [])]
    except Exception:
        return []


def _list_openai_models() -> list[str]:
    """List commonly used OpenAI models."""
    return [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "o1-preview",
        "o1-mini",
    ]


def _list_anthropic_models() -> list[str]:
    """List commonly used Anthropic/Claude models."""
    return [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]


def test_connection(settings: Any) -> tuple[bool, str]:
    """
    Test connection to the configured LLM provider.
    
    Args:
        settings: Settings object with get() method
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    provider = settings.get("llm_provider", "ollama")
    
    try:
        if provider == LLMProvider.OLLAMA:
            return _test_ollama_connection()
        elif provider == LLMProvider.LMSTUDIO:
            return _test_lmstudio_connection(settings)
        elif provider == LLMProvider.OPENAI:
            return _test_openai_connection(settings)
        elif provider == LLMProvider.ANTHROPIC:
            return _test_anthropic_connection(settings)
        else:
            return False, f"Unknown provider: {provider}"
    except Exception as e:
        return False, f"Connection test failed: {str(e)}"


def _test_ollama_connection() -> tuple[bool, str]:
    """Test Ollama connection."""
    try:
        import ollama
        models = ollama.list()
        return True, f"Connected to Ollama ({len(models.models)} models available)"
    except Exception as e:
        return False, f"Cannot connect to Ollama: {str(e)}"


def _test_lmstudio_connection(settings: Any) -> tuple[bool, str]:
    """Test LM Studio connection."""
    try:
        import httpx
        base_url = settings.get("lmstudio_base_url", "http://localhost:1234/v1")
        api_key = settings.get("lmstudio_api_key", "lm-studio")
        
        response = httpx.get(
            f"{base_url}/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5.0,
        )
        response.raise_for_status()
        data = response.json()
        model_count = len(data.get("data", []))
        return True, f"Connected to LM Studio ({model_count} models available)"
    except httpx.TimeoutException:
        return False, "Connection timeout - is LM Studio running?"
    except httpx.ConnectError:
        return False, f"Cannot connect to {base_url} - check if LM Studio is running"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"
