from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, Dict, Any


def compute_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def inventory_prompts(base_dir: Path) -> Iterable[Dict[str, Any]]:
    """Scan markdown/txt files and yield manifest entries.

    A real implementation will later handle embeddings, lineage, roles.
    """
    for path in base_dir.rglob("*.md"):
        content = path.read_text(encoding="utf-8")
        yield {
            "id": path.stem,
            "version": "v1.0.0",
            "role": "system",
            "sha256": compute_sha256(content),
            "template": content,
            "path": str(path.relative_to(base_dir))
        }
