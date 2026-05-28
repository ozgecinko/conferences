"""A minimal SQLite-backed memory store.

This is the demo store from the talk. It is intentionally small so the
core ideas are visible:

  - remember()  : write a fact
  - recall()    : read facts active at a given time  (the ``at=`` magic)
  - replace_fact(): the supersedes pattern (forgetting = deactivating)
  - delete_user(): one-query GDPR deletion (everything is user-scoped)

In production you would back this with Postgres (jsonb / pgvector) or
DynamoDB. The pattern is identical; only the backend changes.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from .records import SemanticFact, SourceType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt is not None else None


def _parse(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value is not None else None


class MemoryStore:
    """SQLite-backed store for SemanticFact records."""

    def __init__(self, path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id          TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL,
                key         TEXT NOT NULL,
                value       TEXT NOT NULL,
                observed_at TEXT NOT NULL,
                valid_from  TEXT NOT NULL,
                valid_until TEXT,
                source      TEXT NOT NULL,
                confidence  REAL NOT NULL,
                supersedes  TEXT
            )
            """
        )
        # Scoping by user_id is what makes GDPR deletion a one-liner.
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_key "
            "ON memories (user_id, key)"
        )
        self.conn.commit()

    # ------------------------------------------------------------------ write

    def add(self, fact: SemanticFact) -> SemanticFact:
        """Insert a fully-built SemanticFact."""
        self.conn.execute(
            """
            INSERT INTO memories
              (id, user_id, key, value, observed_at, valid_from,
               valid_until, source, confidence, supersedes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fact.id,
                fact.user_id,
                fact.key,
                fact.value,
                _iso(fact.observed_at),
                _iso(fact.valid_from),
                _iso(fact.valid_until),
                fact.source.value,
                fact.confidence,
                fact.supersedes,
            ),
        )
        self.conn.commit()
        return fact

    def remember(
        self,
        *,
        user_id: str,
        key: str,
        value: str,
        observed_at: datetime | None = None,
        valid_from: datetime | None = None,
        valid_until: datetime | None = None,
        source: SourceType = SourceType.USER_STATED,
        confidence: float = 1.0,
        supersedes: str | None = None,
    ) -> SemanticFact:
        """Convenience constructor + insert. Defaults timestamps to now (UTC)."""
        now = _utcnow()
        fact = SemanticFact(
            user_id=user_id,
            key=key,
            value=value,
            observed_at=observed_at or now,
            valid_from=valid_from or now,
            valid_until=valid_until,
            source=source,
            confidence=confidence,
            supersedes=supersedes,
        )
        return self.add(fact)

    # ------------------------------------------------------------------- read

    def _row_to_fact(self, row: sqlite3.Row) -> SemanticFact:
        return SemanticFact(
            id=row["id"],
            user_id=row["user_id"],
            key=row["key"],
            value=row["value"],
            observed_at=_parse(row["observed_at"]),
            valid_from=_parse(row["valid_from"]),
            valid_until=_parse(row["valid_until"]),
            source=SourceType(row["source"]),
            confidence=row["confidence"],
            supersedes=row["supersedes"],
        )

    def recall(
        self,
        *,
        user_id: str,
        key: str | None = None,
        at: datetime | None = None,
    ) -> list[SemanticFact]:
        """Return facts active at ``at`` (defaults to now).

        This is the core query. The ``at`` parameter lets you ask not just
        "what is true now?" but "what was true on any past date?" — which
        is a debugging superpower.

        Results are ordered by confidence, then recency, so the most
        trustworthy fact comes first when several match.
        """
        at = at or _utcnow()
        params: list[object] = [user_id]
        sql = "SELECT * FROM memories WHERE user_id = ?"
        if key is not None:
            sql += " AND key = ?"
            params.append(key)

        rows = self.conn.execute(sql, params).fetchall()
        facts = [self._row_to_fact(r) for r in rows]
        active = [f for f in facts if f.is_active(at)]
        active.sort(key=lambda f: (f.confidence, f.observed_at), reverse=True)
        return active

    def recall_one(
        self,
        *,
        user_id: str,
        key: str,
        at: datetime | None = None,
    ) -> SemanticFact | None:
        """Return the single best active fact for a key, or None."""
        results = self.recall(user_id=user_id, key=key, at=at)
        return results[0] if results else None

    def history(self, *, user_id: str, key: str) -> list[SemanticFact]:
        """Return ALL records for a key (active or not), newest first.

        Useful for audit: "show me everything we ever believed about this."
        """
        rows = self.conn.execute(
            "SELECT * FROM memories WHERE user_id = ? AND key = ?",
            (user_id, key),
        ).fetchall()
        facts = [self._row_to_fact(r) for r in rows]
        facts.sort(key=lambda f: f.observed_at, reverse=True)
        return facts

    # ---------------------------------------------------------------- forget

    def replace_fact(
        self,
        *,
        user_id: str,
        key: str,
        new_value: str,
        source: SourceType = SourceType.USER_STATED,
        confidence: float = 1.0,
    ) -> SemanticFact:
        """The supersedes pattern.

        Forgetting is not deleting. We close the old record's validity
        window and insert a new record that links back to it. The old
        fact stays in the database (queryable via history()), it just
        stops being 'active'.
        """
        now = _utcnow()
        old = self.recall_one(user_id=user_id, key=key, at=now)

        if old is not None:
            # Close the old record: persist valid_until = now.
            self.conn.execute(
                "UPDATE memories SET valid_until = ? WHERE id = ?",
                (_iso(now), old.id),
            )
            self.conn.commit()

        return self.remember(
            user_id=user_id,
            key=key,
            value=new_value,
            observed_at=now,
            valid_from=now,
            source=source,
            confidence=confidence,
            supersedes=old.id if old else None,
        )

    def delete_user(self, user_id: str) -> int:
        """GDPR right-to-be-forgotten: delete everything for one user.

        Because every record is scoped by user_id, this is one query.
        Returns the number of rows deleted.
        """
        cur = self.conn.execute(
            "DELETE FROM memories WHERE user_id = ?", (user_id,)
        )
        self.conn.commit()
        return cur.rowcount

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "MemoryStore":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
