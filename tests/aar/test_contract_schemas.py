import json
from pathlib import Path
import re
import pytest

import jsonschema

SCHEMA_DIR = Path('contracts/json')
SCHEMAS = [
    'agent.schema.json',
    'function.schema.json',
    'prompt_asset.schema.json',
]

@pytest.mark.parametrize('schema_name', SCHEMAS)
def test_schema_loads_and_is_valid_draft2020(schema_name):
    path = SCHEMA_DIR / schema_name
    with path.open('r', encoding='utf-8') as f:
        schema = json.load(f)
    # basic required keys
    assert '$schema' in schema
    assert 'title' in schema
    assert 'type' in schema
    assert schema['type'] == 'object'
    # compile validator to ensure internal correctness
    jsonschema.Draft202012Validator.check_schema(schema)


def test_function_schema_param_pattern_allows_valid_identifiers():
    schema = json.loads((SCHEMA_DIR / 'function.schema.json').read_text())
    params = schema['properties']['params']
    pattern = params['propertyNames']['pattern']
    regex = re.compile(pattern)
    # Accept typical identifiers
    for name in ['x', 'arg1', 'param_name', 'CTX_userId']:
        assert regex.match(name), f"Should accept: {name}"
    # Reject invalid ones
    for name in ['1bad', 'hyphen-name', 'space name', '']:
        assert not regex.match(name), f"Should reject: {name}"
