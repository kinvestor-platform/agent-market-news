from collections.abc import Callable
from typing import Any


def tool(name: str, description: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        func._is_tool = True  # type: ignore[attr-defined]
        func._tool_name = name  # type: ignore[attr-defined]
        func._tool_description = description  # type: ignore[attr-defined]
        return func
    return decorator
