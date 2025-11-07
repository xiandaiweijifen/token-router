from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Dict, List


class AllocationError(Exception):
    """Base exception for allocation failures."""


class OverloadedError(AllocationError):
    """Raised when no node has enough remaining quota."""


class DuplicateRequestError(AllocationError):
    """Raised when a request is replayed with different parameters."""


class FreeError(Exception):
    """Base exception for release failures."""


class NotFoundError(FreeError):
    """Raised when attempting to free an unknown request_id."""


@dataclass(frozen=True)
class AllocationRecord:
    node_id: int
    token_count: int


@dataclass(frozen=True)
class AllocationResult:
    node_id: int
    remaining_quota: int


class TokenAllocator:
    """In-memory token allocator with per-node quota tracking."""

    def __init__(self, node_count: int, node_quota: int) -> None:
        if node_count <= 0:
            raise ValueError("node_count must be positive")
        if node_quota <= 0:
            raise ValueError("node_quota must be positive")

        self._lock = Lock()
        self._node_quota = node_quota
        self._tie_break_counter = 0
        self._remaining: List[int] = [node_quota for _ in range(node_count)]
        self._allocations: Dict[str, AllocationRecord] = {}

    def allocate(self, request_id: str, token_count: int) -> AllocationResult:
        if not request_id:
            raise ValueError("request_id is required")
        if token_count <= 0:
            raise ValueError("token_count must be positive")

        with self._lock:
            if request_id in self._allocations:
                record = self._allocations[request_id]
                if record.token_count != token_count:
                    raise DuplicateRequestError(
                        "request_id already allocated with different token_count"
                    )
                return AllocationResult(
                    node_id=record.node_id,
                    remaining_quota=self._remaining[record.node_id],
                )

            node_id = self._select_node(token_count)
            if node_id is None:
                raise OverloadedError("insufficient quota across all nodes")

            self._remaining[node_id] -= token_count
            self._allocations[request_id] = AllocationRecord(node_id, token_count)
            return AllocationResult(
                node_id=node_id,
                remaining_quota=self._remaining[node_id],
            )

    def free(self, request_id: str) -> AllocationRecord:
        if not request_id:
            raise ValueError("request_id is required")

        with self._lock:
            record = self._allocations.pop(request_id, None)
            if record is None:
                raise NotFoundError("request_id not found")

            self._remaining[record.node_id] += record.token_count
            # Cap at node_quota to guard against logic mistakes.
            if self._remaining[record.node_id] > self._node_quota:
                self._remaining[record.node_id] = self._node_quota
            return record

    def stats(self) -> List[int]:
        """Return a copy of the per-node remaining quota."""
        with self._lock:
            return list(self._remaining)

    def _select_node(self, token_count: int) -> int | None:
        """Pick the node with the most remaining capacity that can satisfy the request."""
        best_candidates = []
        max_remaining = -1
        for node_id, remaining in enumerate(self._remaining):
            if remaining < token_count:
                continue
            if remaining > max_remaining:
                best_candidates = [node_id]
                max_remaining = remaining
            elif remaining == max_remaining:
                best_candidates.append(node_id)

        if not best_candidates:
            return None

        selected_index = best_candidates[self._tie_break_counter % len(best_candidates)]
        self._tie_break_counter += 1
        return selected_index
