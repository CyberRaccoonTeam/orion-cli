"""Stub implementation of langgraph.prebuilt.create_react_agent.

The returned agent is a minimal object with `invoke` and `stream`
methods that return empty results or raise informative errors. This
prevents import-time failures while making it explicit that the
real `langgraph` package is required for agent functionality.
"""
from typing import Any, Generator


class _StubAgent:
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def invoke(self, payload: dict) -> dict:
        raise RuntimeError(
            "langgraph.create_react_agent returned a stub agent.\n"
            "Install the 'langgraph' package (pip install langgraph) to enable full agent features."
        )

    def stream(self, payload: dict, **kwargs) -> Generator[Any, None, None]:
        raise RuntimeError(
            "langgraph.create_react_agent returned a stub agent.\n"
            "Install the 'langgraph' package (pip install langgraph) to enable streaming agent features."
        )


def create_react_agent(*args, **kwargs) -> _StubAgent:
    """Return a stub agent object in lieu of the real LangGraph agent.

    Callers should install `langgraph` to get the full implementation.
    """
    return _StubAgent(*args, **kwargs)

__all__ = ["create_react_agent"]
