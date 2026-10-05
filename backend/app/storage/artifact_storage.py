from pathlib import Path


class ArtifactStorage:
    """Resolve registered artifact paths within the configured storage root."""

    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root.resolve()

    def resolve_registered_path(self, safe_relative_path: str) -> Path:
        """Resolve a registered relative path and prevent path traversal."""
        relative_path = Path(safe_relative_path)

        if relative_path.is_absolute():
            raise ValueError("Artifact path must be relative.")

        resolved_path = (self.storage_root / relative_path).resolve()

        try:
            resolved_path.relative_to(self.storage_root)
        except ValueError as exc:
            raise ValueError("Artifact path escapes storage root.") from exc

        return resolved_path

    def ensure_exists(self, safe_relative_path: str) -> Path:
        """Resolve a registered artifact and require the file to exist."""
        path = self.resolve_registered_path(safe_relative_path)

        if not path.is_file():
            raise FileNotFoundError(
                f"Registered artifact is missing: {safe_relative_path}"
            )

        return path