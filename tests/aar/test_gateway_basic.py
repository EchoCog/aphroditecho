from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from aphrodite.aar_core.gateway import AARGateway


def test_gateway_lists_agents_and_functions(tmp_path: Path):
    gw = AARGateway(contracts_dir=tmp_path)

    gw.register_agent({
        "id": "agent.demo",
        "version": "v1.0.0",
        "capabilities": ["chat"],
        "tools_allow": [],
        "policies": [],
        "prompt_profile": "default"
    })

    def ping():
        return "pong"

    gw.functions.register(
        ping,
        name="sys.ping",
        description="Ping function",
        params_schema={"type": "object", "properties": {}},
        safety_class="low",
        cost_unit=0.0,
    )

    app = FastAPI()
    app.include_router(gw.router, prefix="/aar")
    client = TestClient(app)

    agents_resp = client.get("/aar/agents").json()
    assert agents_resp[0]["id"] == "agent.demo"

    funcs_resp = client.get("/aar/functions").json()
    assert funcs_resp[0]["name"] == "sys.ping"

    invoke_resp = client.post("/aar/functions/invoke/sys.ping", json={}).json()
    assert invoke_resp["result"] == "pong"
