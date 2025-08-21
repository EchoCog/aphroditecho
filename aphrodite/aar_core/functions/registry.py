from __future__ import annotations

import inspect
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class RegisteredFunction:
    name: str
    description: str
    params_schema: Dict[str, Any]
    safety_class: str
    cost_unit: float
    callable: Callable[..., Any]
    tags: List[str] = field(default_factory=list)

    def invoke(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Basic parameter filtering (future: full JSON Schema validation)
        sig = inspect.signature(self.callable)
        kwargs = {k: v for k, v in payload.items() if k in sig.parameters}
        start = time.perf_counter()
        result = self.callable(**kwargs)
        duration = time.perf_counter() - start
        return {"result": result, "latency_ms": duration * 1000.0}


class FunctionRegistry:
    def __init__(self) -> None:
        self._functions: Dict[str, RegisteredFunction] = {}

    def register(self, fn: Callable[..., Any], *, name: str, description: str, params_schema: Dict[str, Any], safety_class: str = "low", cost_unit: float = 0.0, tags: List[str] | None = None) -> None:
        if name in self._functions:
            raise ValueError(f"Function '{name}' already registered")
        self._functions[name] = RegisteredFunction(
            name=name,
            description=description,
            params_schema=params_schema,
            safety_class=safety_class,
            cost_unit=cost_unit,
            callable=fn,
            tags=tags or [],
        )

    def has(self, name: str) -> bool:
        return name in self._functions

    def list_functions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": f.name,
                "description": f.description,
                "safety_class": f.safety_class,
                "cost_unit": f.cost_unit,
                "tags": f.tags,
                "params_schema": f.params_schema,
            }
            for f in self._functions.values()
        ]

    def invoke(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self._functions:
            raise KeyError(name)
        return self._functions[name].invoke(payload)
