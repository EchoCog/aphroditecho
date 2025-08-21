#!/usr/bin/env python
from __future__ import annotations

import json
from pathlib import Path

from echo.sys.prompt_kernel.inventory import inventory_prompts  # type: ignore  # noqa: F401


def main():
    root = Path(__file__).resolve().parents[1] / "echo.sys"
    prompts_dir = root
    manifest = list(inventory_prompts(prompts_dir))
    out_path = root / "prompt_manifest.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Wrote {len(manifest)} prompts to {out_path}")


if __name__ == "__main__":  # pragma: no cover
    main()
