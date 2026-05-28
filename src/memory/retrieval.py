"""Retrieval and write-time defenses.

Two failure modes from the talk get their fixes here:

  - Context pollution -> retrieve_context(): filter early, cap quantity,
    enforce a relevance floor and a recency cutoff, label everything.
  - Memory poisoning  -> safe_write(): reject instruction-like content,
    tag provenance and trust, never auto-trust external sources.

The relevance scorer here is a trivial keyword overlap so the demo runs
with no dependencies. In production you would swap in embedding
similarity — the *shape* of the function stays the same.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .records import SemanticFact, SourceType
from .store import MemoryStore


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------- pollution

def _keyword_overlap(query: str, text: str) -> float:
    """Toy relevance score in [0, 1]. Replace with embedding similarity."""
    q = set(re.findall(r"\w+", query.lower()))
    t = set(re.findall(r"\w+", text.lower()))
    if not q or not t:
        return 0.0
    return len(q & t) / len(q)


@dataclass(frozen=True)
class RetrievedMemory:
    """A memory plus the metadata the model needs to interpret it."""

    fact: SemanticFact
    relevance: float

    def as_labeled_text(self) -> str:
        """Render with source + timestamp so the model knows what it reads."""
        observed = self.fact.observed_at.date().isoformat()
        return (
            f"[{self.fact.source.value}, observed {observed}, "
            f"confidence {self.fact.confidence:.1f}] "
            f"{self.fact.key}: {self.fact.value}"
        )


def retrieve_context(
    store: MemoryStore,
    *,
    user_id: str,
    query: str,
    top_k: int = 5,
    min_relevance: float = 0.3,
    max_age: timedelta | None = timedelta(days=30),
    at: datetime | None = None,
) -> list[RetrievedMemory]:
    """Retrieve with constraints — the fix for context pollution.

    Filter first (user, validity, recency), then rank by relevance, then
    cap with top_k. Don't dump everything into the prompt and hope.
    """
    at = at or _utcnow()
    candidates = store.recall(user_id=user_id, at=at)

    scored: list[RetrievedMemory] = []
    for fact in candidates:
        if max_age is not None and (at - fact.observed_at) > max_age:
            continue
        relevance = _keyword_overlap(query, f"{fact.key} {fact.value}")
        if relevance < min_relevance:
            continue
        scored.append(RetrievedMemory(fact=fact, relevance=relevance))

    scored.sort(
        key=lambda m: (m.relevance, m.fact.confidence),
        reverse=True,
    )
    return scored[:top_k]


# --------------------------------------------------------------------- poisoning

_INSTRUCTION_PATTERNS = (
    r"\bignore (the |all |previous )?(above|prior|earlier|instructions)\b",
    r"\bwhen asked\b",
    r"\byou (must|should|will|always|never)\b",
    r"\brecommend\b.*\binstead\b",
    r"\bsystem prompt\b",
    r"\boverride\b",
)


def looks_like_instruction(text: str) -> bool:
    """Heuristic: does this candidate memory try to command the model?

    Memory should hold *facts*, not *commands*. Anything that reads like
    an instruction is a poisoning red flag.
    """
    low = text.lower()
    return any(re.search(p, low) for p in _INSTRUCTION_PATTERNS)


class MemoryRejected(Exception):
    """Raised when a candidate memory fails the write-time safety check."""


def safe_write(
    store: MemoryStore,
    *,
    user_id: str,
    key: str,
    value: str,
    source: SourceType,
) -> SemanticFact:
    """Write-time defense for memory poisoning.

    Rules:
      1. Reject instruction-like content outright.
      2. Confidence is capped by the source's trust level.
      3. External content is never auto-trusted at full confidence.
    """
    if looks_like_instruction(value):
        raise MemoryRejected("memory cannot contain instructions")

    # Map trust level (1..5) onto a confidence ceiling.
    confidence_ceiling = source.trust_level / 5.0

    return store.remember(
        user_id=user_id,
        key=key,
        value=value,
        source=source,
        confidence=confidence_ceiling,
    )
