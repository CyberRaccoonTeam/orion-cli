"""Minimal shim for `langchain_ollama` to avoid import-time failures.

This provides a placeholder `ChatOllama` class that raises a clear
error when methods that require Ollama are called. For full
functionality install the upstream `langchain-ollama` package and
ensure the `ollama` runtime is available.
"""
from typing import Any


class ChatOllama:
    def __init__(self, *args, **kwargs):
        self._init_args = args
        self._init_kwargs = kwargs

    def invoke(self, messages: list) -> Any:
        raise RuntimeError(
            "ChatOllama is a stub: install the 'langchain-ollama' package and configure Ollama to use LLM features."
        )

    def stream(self, messages: list, **kwargs):
        raise RuntimeError(
            "ChatOllama.stream is a stub: install the 'langchain-ollama' package and configure Ollama to use streaming."
        )

__all__ = ["ChatOllama"]
