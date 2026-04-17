"""Compatibility shim for projects importing `langchain_core`.

This package re-exports the commonly used `messages` and `tools`
submodules either from a real `langchain_core` installation or from
`langchain` (older package layout). If neither is available it
provides lightweight fallback implementations sufficient for local
execution in this repository.
"""
from . import messages  # noqa: F401
from . import tools  # noqa: F401

__all__ = ["messages", "tools"]
