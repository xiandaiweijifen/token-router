from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AppConfig:
    node_count: int
    node_quota: int


DEFAULT_NODE_COUNT = 3
DEFAULT_NODE_QUOTA = 300


def load_config() -> AppConfig:
    """Read allocator configuration from environment (with sane defaults)."""
    node_count = _read_positive_int("TOKEN_ROUTER_NODE_COUNT", DEFAULT_NODE_COUNT)
    node_quota = _read_positive_int("TOKEN_ROUTER_NODE_QUOTA", DEFAULT_NODE_QUOTA)
    return AppConfig(node_count=node_count, node_quota=node_quota)


def _read_positive_int(env_key: str, default: int) -> int:
    """Parse a positive integer environment variable or fall back to `default`."""
    raw_value = os.getenv(env_key)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{env_key} must be an integer") from exc
    if value <= 0:
        raise ValueError(f"{env_key} must be positive")
    return value
