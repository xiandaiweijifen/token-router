import pytest

from app.token_allocator import (
    DuplicateRequestError,
    NotFoundError,
    OverloadedError,
    TokenAllocator,
)


def test_allocate_and_free_updates_quota() -> None:
    allocator = TokenAllocator(node_count=2, node_quota=100)

    result = allocator.allocate("req-1", 60)
    assert result.remaining_quota == 40

    record = allocator.free("req-1")
    assert record.node_id == result.node_id
    assert allocator.stats()[record.node_id] == 100


def test_duplicate_request_is_idempotent() -> None:
    allocator = TokenAllocator(node_count=1, node_quota=50)
    first = allocator.allocate("req-1", 20)
    second = allocator.allocate("req-1", 20)
    assert first == second


def test_duplicate_request_with_different_token_count_raises() -> None:
    allocator = TokenAllocator(node_count=1, node_quota=50)
    allocator.allocate("req-1", 20)

    with pytest.raises(DuplicateRequestError):
        allocator.allocate("req-1", 10)


def test_overloaded_when_no_node_has_enough_quota() -> None:
    allocator = TokenAllocator(node_count=2, node_quota=30)
    allocator.allocate("req-1", 30)
    allocator.allocate("req-2", 30)

    with pytest.raises(OverloadedError):
        allocator.allocate("req-3", 10)


def test_free_unknown_request_id_raises() -> None:
    allocator = TokenAllocator(node_count=1, node_quota=50)

    with pytest.raises(NotFoundError):
        allocator.free("missing")


def test_allocator_picks_node_with_most_remaining_capacity() -> None:
    allocator = TokenAllocator(node_count=3, node_quota=100)
    allocator.allocate("req-1", 90)
    allocator.allocate("req-2", 10)

    result = allocator.allocate("req-3", 50)
    # Node 2 retains the full 100 quota before this request, so it should be chosen.
    assert result.node_id == 2
    assert result.remaining_quota == 50


def test_allocator_round_robins_among_equal_nodes() -> None:
    allocator = TokenAllocator(node_count=2, node_quota=100)

    first = allocator.allocate("req-1", 10)
    allocator.free("req-1")

    second = allocator.allocate("req-2", 10)
    allocator.free("req-2")

    third = allocator.allocate("req-3", 10)
    allocator.free("req-3")

    assert first.node_id == 0
    assert second.node_id == 1
    assert third.node_id == 0
