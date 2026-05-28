"""Memory record types.

The three long-term memory types from the talk, plus the source/trust
enums used for poisoning defense.

  - SemanticFact : "what I know"   (facts about the user / world)
  - Episode      : "what happened" (time-ordered events)
  - Policy       : "how to do it"  (rules and behaviors)

The design idea: memory is a data-modeling problem with *temporal
semantics*. Every fact knows when it was learned, when it became true,
and when it stopped being true.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum


def _new_id() -> str:
    return uuid.uuid4().hex


class SourceType(str, Enum):
    """Where a memory came from. Used to gate trust (poisoning defense)."""

    USER_STATED = "user_stated"      # the user said it directly  -> trust 5
    USER_IMPLIED = "user_implied"    # we inferred it from context -> trust 3
    EXTERNAL_DOC = "external_doc"    # extracted from a document   -> trust 1

    @property
    def trust_level(self) -> int:
        return {"user_stated": 5, "user_implied": 3, "external_doc": 1}[self.value]


@dataclass(frozen=True)
class SemanticFact:
    """A fact about the user or the world.

    The three time fields are the heart of the design:
      - observed_at : when *we* learned it
      - valid_from  : when it *became true* in the world
      - valid_until : when it *stopped* being true (None = still true)

    Separating "when we learned it" from "when it was true" is bitemporal
    modeling. It is what lets us answer "what did we know on date X?".
    """

    user_id: str
    key: str
    value: str

    observed_at: datetime
    valid_from: datetime
    valid_until: datetime | None = None

    source: SourceType = SourceType.USER_STATED
    confidence: float = 1.0

    id: str = field(default_factory=_new_id)
    supersedes: str | None = None

    def is_active(self, at: datetime) -> bool:
        """Was this fact active at the given moment?"""
        if at < self.valid_from:
            return False
        if self.valid_until is not None and at >= self.valid_until:
            return False
        return True

    def closed(self, at: datetime) -> SemanticFact:
        """Return a copy with the validity window closed at ``at``.

        Frozen dataclasses are immutable, so 'deactivating' a record
        means producing a new record with valid_until set.
        """
        return replace(self, valid_until=at)


@dataclass(frozen=True)
class Episode:
    """A time-stamped event. Episodic memory is a journal: order matters."""

    user_id: str
    timestamp: datetime
    event_type: str            # e.g. "user_query", "agent_action"
    summary: str
    context: dict = field(default_factory=dict)

    importance: float = 0.5    # 0.0 .. 1.0

    id: str = field(default_factory=_new_id)


@dataclass(frozen=True)
class Policy:
    """A rule the agent follows. Procedural memory: "how to do it"."""

    name: str
    when: str                  # condition / trigger (natural language)
    then: str                  # action / behavior
    priority: int = 0          # higher = applied first
    confidence: float = 1.0

    id: str = field(default_factory=_new_id)
