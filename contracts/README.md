# Contracts

Versioned JSON Schemas and protobuf IDL defining cross-language stable contracts for AAR gateway, functions, agents, prompts, memory, and relations.

Change policy:

1. Additive changes only in same major version.
2. Breaking changes require major version bump and migration notes.
3. CI enforces backward compatibility via schema diff tests.

Schemas:

- `agent.schema.json`
- `function.schema.json`
- `prompt_asset.schema.json`

Protobuf (planned):

- `gateway.proto`
- `memory.proto`
- `functions.proto`
