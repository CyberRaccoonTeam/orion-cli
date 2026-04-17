"""Provide `AIMessage`, `HumanMessage`, `SystemMessage`, `ToolMessage`.

Try to import from an installed `langchain_core` first, then fall back
to `langchain.schema`. If neither is available, provide minimal
implementations used by this project.
"""
try:
    # Prefer the real package if available
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage  # type: ignore
except Exception:
    try:
        # Fallback for older langchain versions
        from langchain.schema import AIMessage, HumanMessage, SystemMessage, ToolMessage  # type: ignore
    except Exception:
        # Minimal local implementations
        class _BaseMessage:
            def __init__(self, content: str = "", **kwargs):
                self.content = content

        class AIMessage(_BaseMessage):
            pass

        class HumanMessage(_BaseMessage):
            pass

        class SystemMessage(_BaseMessage):
            pass

        class ToolMessage(_BaseMessage):
            def __init__(self, content: str = "", tool_call_id: str | None = None, name: str | None = None, **kwargs):
                super().__init__(content, **kwargs)
                self.tool_call_id = tool_call_id
                self.name = name

__all__ = ["AIMessage", "HumanMessage", "SystemMessage", "ToolMessage"]
