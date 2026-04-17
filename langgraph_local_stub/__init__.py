"""Lightweight shim for `langgraph` to avoid import-time failures.

This provides the `prebuilt` submodule with a `create_react_agent`
factory that returns a stub agent. The stub agent implements
`invoke` and `stream` methods used by Orion but raises a clear
RuntimeError when invoked to indicate the real `langgraph` package
should be installed for full functionality.
"""
from . import prebuilt  # noqa: F401

__all__ = ["prebuilt"]
