"""Temporal memory tests.

The headline test from the talk:
    "If you can't write this test, your memory architecture is broken."
"""

from datetime import datetime, timezone

import pytest

from memory import MemoryStore, SemanticFact, SourceType

UTC = timezone.utc


@pytest.fixture
def store():
    s = MemoryStore()  # in-memory SQLite
    yield s
    s.close()


def test_expired_memory_is_not_recalled(store):
    """The slide-29 test: an expired fact must not come back."""
    store.remember(
        user_id="u-1",
        key="language",
        value="Java",
        valid_from=datetime(2024, 1, 1, tzinfo=UTC),
        valid_until=datetime(2025, 1, 1, tzinfo=UTC),
    )

    records = store.recall(
        user_id="u-1",
        key="language",
        at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert records == []


def test_active_memory_is_recalled(store):
    """A fact inside its validity window comes back."""
    store.remember(
        user_id="u-1",
        key="language",
        value="Python",
        valid_from=datetime(2025, 1, 1, tzinfo=UTC),
        valid_until=None,  # still true
    )

    result = store.recall_one(
        user_id="u-1",
        key="language",
        at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert result is not None
    assert result.value == "Python"


def test_recall_at_past_date(store):
    """The 'at=' superpower: query what was true on a past date."""
    store.remember(
        user_id="u-1",
        key="company",
        value="Acme Corp",
        valid_from=datetime(2023, 1, 10, tzinfo=UTC),
        valid_until=datetime(2024, 9, 1, tzinfo=UTC),
    )

    # During the window -> active
    during = store.recall_one(
        user_id="u-1", key="company",
        at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    assert during is not None and during.value == "Acme Corp"

    # After the window -> gone
    after = store.recall_one(
        user_id="u-1", key="company",
        at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    assert after is None


def test_is_active_boundaries():
    """valid_from is inclusive, valid_until is exclusive."""
    fact = SemanticFact(
        user_id="u-1",
        key="k",
        value="v",
        observed_at=datetime(2024, 1, 1, tzinfo=UTC),
        valid_from=datetime(2024, 1, 1, tzinfo=UTC),
        valid_until=datetime(2024, 12, 31, tzinfo=UTC),
    )

    assert fact.is_active(datetime(2024, 1, 1, tzinfo=UTC)) is True   # start
    assert fact.is_active(datetime(2024, 6, 1, tzinfo=UTC)) is True   # middle
    assert fact.is_active(datetime(2023, 12, 31, tzinfo=UTC)) is False  # before
    assert fact.is_active(datetime(2024, 12, 31, tzinfo=UTC)) is False  # end (exclusive)


def test_confidence_ordering(store):
    """When two facts match, higher confidence wins."""
    now = datetime(2026, 1, 1, tzinfo=UTC)
    store.remember(
        user_id="u-1", key="city", value="Berlin",
        valid_from=datetime(2025, 1, 1, tzinfo=UTC), confidence=0.6,
    )
    store.remember(
        user_id="u-1", key="city", value="Istanbul",
        valid_from=datetime(2025, 1, 1, tzinfo=UTC), confidence=1.0,
    )

    best = store.recall_one(user_id="u-1", key="city", at=now)
    assert best.value == "Istanbul"
