"""Provide `tool` decorator and `StructuredTool` shim.

This attempts to import the real implementations from `langchain_core`
or `langchain`. If unavailable, it provides small compatible
implementations used by the project (a simple `tool` decorator and a
`StructuredTool` factory exposing `from_function`).
"""
from typing import Callable, Any

try:
    from langchain_core.tools import tool, StructuredTool  # type: ignore
except Exception:
    try:
        from langchain.tools import tool, StructuredTool  # type: ignore
    except Exception:
        # Simple decorator to mark a function as a tool. It returns the
        # function unchanged but sets an attribute that other code can
        # inspect if needed.
        class _ToolWrapper:
            def __init__(self, func: Callable, name: str | None = None, description: str | None = None):
                self._func = func
                self.name = name or getattr(func, "__name__", "tool")
                self.description = description or (getattr(func, "__doc__", "") or "")

            def invoke(self, args: dict | None = None):
                args = args or {}
                try:
                    return self._func(**args)
                except TypeError:
                    return self._func()

            def __call__(self, *a, **kw):
                return self._func(*a, **kw)

        def tool(func: Callable | None = None, **kwargs):
            name = kwargs.get("name")
            description = kwargs.get("description")
            if func is None:
                def _wrapper(f: Callable):
                    return _ToolWrapper(f, name=name, description=description)
                return _wrapper
            return _ToolWrapper(func, name=name, description=description)

        class StructuredTool:
            """Very small StructuredTool substitute exposing `from_function`.

            The returned object exposes `.name`, `.description` and an
            `invoke(args: dict)` method expected by this repository.
            """

            def __init__(self, func: Callable, name: str | None = None, description: str | None = None):
                # If func is already a _ToolWrapper or similar, extract attributes
                if hasattr(func, "name") and hasattr(func, "invoke"):
                    self._func = func
                    self.name = getattr(func, "name")
                    self.description = getattr(func, "description", "")
                else:
                    self._func = func
                    self.name = name or getattr(func, "__name__", "tool")
                    self.description = description or (getattr(func, "__doc__", "") or "")

            @classmethod
            def from_function(cls, func: Callable, name: str | None = None, description: str | None = None):
                return cls(func=func, name=name, description=description)

            def invoke(self, args: dict | None = None) -> Any:
                args = args or {}
                # If underlying func has an invoke method, call it
                if hasattr(self._func, "invoke"):
                    return self._func.invoke(args)
                try:
                    return self._func(**args)
                except TypeError:
                    return self._func()

__all__ = ["tool", "StructuredTool"]
