"""
In-memory store mapping game_id (client-generated UUID) to GameEngine instances.
Each browser tab generates its own game_id on page load, avoiding collision when
multiple tabs share the same Flask session cookie.
"""
import time
from typing import Optional

from blackjack.engine import GameEngine

_store: dict[str, dict] = {}  # {game_id: {"engine": GameEngine, "last_accessed": float}}
_TTL_SECONDS = 1800  # 30 minutes


def get_engine(game_id: str) -> Optional[GameEngine]:
    _evict_stale()
    entry = _store.get(game_id)
    if entry is None:
        return None
    entry["last_accessed"] = time.time()
    return entry["engine"]


def create_engine(game_id: str, num_seats: int, mode: str, starting_bankroll: int = 1000) -> GameEngine:
    _evict_stale()
    engine = GameEngine(num_seats=num_seats, mode=mode, starting_bankroll=starting_bankroll)
    _store[game_id] = {"engine": engine, "last_accessed": time.time()}
    return engine


def remove_engine(game_id: str) -> None:
    _store.pop(game_id, None)


def _evict_stale() -> None:
    now = time.time()
    stale = [gid for gid, entry in _store.items() if now - entry["last_accessed"] > _TTL_SECONDS]
    for gid in stale:
        del _store[gid]
