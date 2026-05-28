"""memory — designing memory for AI applications in Python.

Companion code for the PyCon Italia 2026 talk.

Quick start:

    from datetime import datetime, timezone
    from memory import MemoryStore

    store = MemoryStore()                      # in-memory SQLite
    store.remember(user_id="u1", key="diet", value="vegan")

    now = datetime.now(timezone.utc)
    print(store.recall_one(user_id="u1", key="diet", at=now).value)  # "vegan"

    store.replace_fact(user_id="u1", key="diet", new_value="omnivore")
    print(store.recall_one(user_id="u1", key="diet", at=now).value)  # "omnivore"
"""

from .records import Episode, Policy, SemanticFact, SourceType
from .retrieval import (
    MemoryRejected,
    RetrievedMemory,
    looks_like_instruction,
    retrieve_context,
    safe_write,
)
from .store import MemoryStore

__all__ = [
    "SemanticFact",
    "Episode",
    "Policy",
    "SourceType",
    "MemoryStore",
    "RetrievedMemory",
    "retrieve_context",
    "safe_write",
    "looks_like_instruction",
    "MemoryRejected",
]

__version__ = "0.1.0"
