"""Prompt store for managing prompt assets with versioning."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from inventory import compute_sha256


class PromptAsset:
    """Represents a prompt asset with metadata."""
    
    def __init__(
        self,
        id: str,
        version: str,
        role: str,
        template: str,
        tags: Optional[List[str]] = None,
        parent_version: Optional[str] = None,
        embedding_fingerprint: Optional[str] = None,
    ):
        self.id = id
        self.version = version
        self.role = role
        self.template = template
        self.tags = tags or []
        self.parent_version = parent_version
        self.embedding_fingerprint = embedding_fingerprint
        self.sha256 = compute_sha256(template)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "version": self.version,
            "role": self.role,
            "tags": self.tags,
            "sha256": self.sha256,
            "parent_version": self.parent_version,
            "template": self.template,
            "embedding_fingerprint": self.embedding_fingerprint,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PromptAsset:
        """Create from dictionary representation."""
        return cls(
            id=data["id"],
            version=data["version"],
            role=data["role"],
            template=data["template"],
            tags=data.get("tags", []),
            parent_version=data.get("parent_version"),
            embedding_fingerprint=data.get("embedding_fingerprint"),
        )


class PromptStore:
    """Manages prompt assets with versioning and retrieval."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(".")
        self._prompts: Dict[str, PromptAsset] = {}
        self._prompt_versions: Dict[str, List[str]] = {}  # id -> [versions]
        self._role_index: Dict[str, List[str]] = {}  # role -> [ids]
        self._tag_index: Dict[str, List[str]] = {}  # tag -> [ids]
        
        if self.base_dir.exists():
            self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load prompts from the base directory."""
        for path in self.base_dir.rglob("*.md"):
            try:
                content = path.read_text(encoding="utf-8")
                
                # Extract metadata from frontmatter if present
                metadata = self._extract_metadata(content)
                
                prompt = PromptAsset(
                    id=path.stem,
                    version=metadata.get("version", "v1.0.0"),
                    role=metadata.get("role", "system"),
                    template=content,
                    tags=metadata.get("tags", []),
                    parent_version=metadata.get("parent_version"),
                )
                
                self.add_prompt(prompt)
                
            except Exception as e:
                print(f"Warning: Could not load prompt from {path}: {e}")
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from markdown frontmatter."""
        metadata = {}
        
        if content.startswith("---"):
            try:
                end_marker = content.find("---", 3)
                if end_marker != -1:
                    frontmatter = content[3:end_marker].strip()
                    metadata = json.loads(frontmatter)
            except:
                pass
        
        return metadata
    
    def add_prompt(self, prompt: PromptAsset) -> None:
        """Add a prompt to the store."""
        prompt_key = f"{prompt.id}:{prompt.version}"
        self._prompts[prompt_key] = prompt
        
        # Update version index
        if prompt.id not in self._prompt_versions:
            self._prompt_versions[prompt.id] = []
        self._prompt_versions[prompt.id].append(prompt.version)
        
        # Update role index
        if prompt.role not in self._role_index:
            self._role_index[prompt.role] = []
        if prompt.id not in self._role_index[prompt.role]:
            self._role_index[prompt.role].append(prompt.id)
        
        # Update tag index
        for tag in prompt.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            if prompt.id not in self._tag_index[tag]:
                self._tag_index[tag].append(prompt.id)
    
    def get_prompt(self, prompt_id: str, version: Optional[str] = None) -> Optional[PromptAsset]:
        """Get a prompt by ID and optional version."""
        if version is None:
            # Get latest version
            versions = self._prompt_versions.get(prompt_id, [])
            if not versions:
                return None
            version = sorted(versions)[-1]  # Latest version
        
        prompt_key = f"{prompt_id}:{version}"
        return self._prompts.get(prompt_key)
    
    def get_prompts_by_role(self, role: str) -> List[PromptAsset]:
        """Get all prompts for a specific role."""
        prompt_ids = self._role_index.get(role, [])
        prompts = []
        
        for prompt_id in prompt_ids:
            versions = self._prompt_versions.get(prompt_id, [])
            if versions:
                latest_version = sorted(versions)[-1]
                prompt_key = f"{prompt_id}:{latest_version}"
                if prompt_key in self._prompts:
                    prompts.append(self._prompts[prompt_key])
        
        return prompts
    
    def get_prompts_by_tag(self, tag: str) -> List[PromptAsset]:
        """Get all prompts with a specific tag."""
        prompt_ids = self._tag_index.get(tag, [])
        prompts = []
        
        for prompt_id in prompt_ids:
            versions = self._prompt_versions.get(prompt_id, [])
            if versions:
                latest_version = sorted(versions)[-1]
                prompt_key = f"{prompt_id}:{latest_version}"
                if prompt_key in self._prompts:
                    prompts.append(self._prompts[prompt_key])
        
        return prompts
    
    def search_prompts(self, query: str, limit: int = 10) -> List[PromptAsset]:
        """Search prompts by content."""
        results = []
        query_lower = query.lower()
        
        for prompt in self._prompts.values():
            if query_lower in prompt.template.lower():
                results.append(prompt)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_prompt_versions(self, prompt_id: str) -> List[str]:
        """Get all versions of a prompt."""
        return self._prompt_versions.get(prompt_id, [])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the prompt store."""
        total_prompts = len(self._prompts)
        unique_prompts = len(self._prompt_versions)
        roles = list(self._role_index.keys())
        tags = list(self._tag_index.keys())
        
        return {
            "total_prompts": total_prompts,
            "unique_prompts": unique_prompts,
            "roles": roles,
            "tags": tags,
            "role_count": len(roles),
            "tag_count": len(tags),
        }