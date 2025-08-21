from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException

from aphrodite.aar_core.functions.registry import FunctionRegistry


class AARGateway:
    """Gateway facade exposing agent, function, and prompt discovery.

    This is an initial production-grade slice (read-only + testable) to be
    expanded with arena lifecycle and memory augmentation.
    """

    def __init__(self, contracts_dir: Path):
        self.contracts_dir = contracts_dir
        self.functions = FunctionRegistry()
        # Agent & prompt specs may later be loaded from persistent store.
        self._agents: Dict[str, Dict[str, Any]] = {}
        self.router = APIRouter()
        self._mount_routes()

    # ---------- Public API ----------
    def register_agent(self, spec: Dict[str, Any]) -> None:
        agent_id = spec.get("id")
        if not agent_id:
            raise ValueError("Agent spec missing 'id'")
        if agent_id in self._agents:
            raise ValueError(f"Agent '{agent_id}' already registered")
        self._agents[agent_id] = spec

    def list_agents(self) -> List[Dict[str, Any]]:
        return list(self._agents.values())

    # ---------- Internal ----------
    def _mount_routes(self) -> None:
        r = self.router

        @r.get("/agents")
        def get_agents() -> List[Dict[str, Any]]:
            return self.list_agents()

        @r.get("/functions")
        def get_functions() -> List[Dict[str, Any]]:
            return self.functions.list_functions()

        @r.post("/functions/invoke/{name}")
        def invoke_function(name: str, payload: Dict[str, Any]):
            if not self.functions.has(name):
                raise HTTPException(status_code=404, detail="Function not found")
            return self.functions.invoke(name, payload)

    # Future: arena lifecycle, memory attach, relation graph queries.


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
