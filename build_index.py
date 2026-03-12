from __future__ import annotations

from src.config import get_settings
from src.rag.index_builder import VectorStoreManager


def main() -> None:
    settings = get_settings()
    manager = VectorStoreManager(settings)
    manager.build_index(rebuild=True)
    count = manager.client.count(
        collection_name=settings.qdrant_collection_name,
        exact=True,
    )
    print(f"chunks in collection: {count.count}")


if __name__ == "__main__":
    main()
