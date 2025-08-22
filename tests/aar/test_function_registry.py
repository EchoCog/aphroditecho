from aphrodite.aar_core.functions.registry import FunctionRegistry


def test_register_and_invoke():
    reg = FunctionRegistry()

    def add(a: int, b: int) -> int:
        return a + b

    reg.register(
        add,
        name="math.add",
        description="Add two integers",
        params_schema={"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}, "required": ["a", "b"]},
        safety_class="low",
        cost_unit=0.1,
        tags=["math"],
    )

    assert reg.has("math.add")
    result = reg.invoke("math.add", {"a": 2, "b": 3})
    assert result["result"] == 5
    assert result["latency_ms"] >= 0.0