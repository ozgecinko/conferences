"""Supersedes-pattern tests: forgetting = deactivating, not deleting."""

from datetime import timezone

import pytest

from memory import MemoryStore

UTC = timezone.utc


@pytest.fixture
def store():
    s = MemoryStore()
    yield s
    s.close()


def test_replace_fact_updates_active_value(store):
    """After replacing, recall returns the new value."""
    store.remember(user_id="u-1", key="diet", value="vegan")
    store.replace_fact(user_id="u-1", key="diet", new_value="omnivore")

    current = store.recall_one(user_id="u-1", key="diet")
    assert current.value == "omnivore"


def test_replace_fact_keeps_history(store):
    """The old fact is NOT deleted — it stays queryable via history()."""
    store.remember(user_id="u-1", key="diet", value="vegan")
    store.replace_fact(user_id="u-1", key="diet", new_value="omnivore")

    history = store.history(user_id="u-1", key="diet")
    values = {f.value for f in history}

    assert values == {"vegan", "omnivore"}
    assert len(history) == 2


def test_supersedes_link_points_to_old_record(store):
    """The new record links back to the one it replaced (audit trail)."""
    old = store.remember(user_id="u-1", key="diet", value="vegan")
    new = store.replace_fact(user_id="u-1", key="diet", new_value="omnivore")

    assert new.supersedes == old.id


def test_only_one_active_after_replace(store):
    """Exactly one record is active after a replace."""
    store.remember(user_id="u-1", key="diet", value="vegan")
    store.replace_fact(user_id="u-1", key="diet", new_value="omnivore")

    active = store.recall(user_id="u-1", key="diet")
    assert len(active) == 1
    assert active[0].value == "omnivore"


def test_delete_user_is_one_query(store):
    """GDPR: deleting a user removes all their records, and only theirs."""
    store.remember(user_id="u-1", key="diet", value="vegan")
    store.remember(user_id="u-1", key="city", value="Istanbul")
    store.remember(user_id="u-2", key="diet", value="omnivore")

    deleted = store.delete_user("u-1")

    assert deleted == 2
    assert store.recall(user_id="u-1") == []
    # Other users are untouched.
    assert store.recall_one(user_id="u-2", key="diet").value == "omnivore"
