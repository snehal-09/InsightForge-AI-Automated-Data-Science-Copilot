"""
Lightweight in-memory session store.
Each uploaded dataset gets a session_id used to retrieve its file path
and cached analysis results across subsequent requests (analyze -> build
notebook -> download), without needing a database.
"""
import threading
from typing import Any

_lock = threading.Lock()
_sessions: dict[str, dict[str, Any]] = {}


def create_session(session_id: str, **data: Any) -> None:
    with _lock:
        _sessions[session_id] = data


def update_session(session_id: str, **data: Any) -> None:
    with _lock:
        if session_id not in _sessions:
            _sessions[session_id] = {}
        _sessions[session_id].update(data)


def get_session(session_id: str) -> dict[str, Any] | None:
    with _lock:
        return _sessions.get(session_id)


def all_sessions() -> dict[str, dict[str, Any]]:
    with _lock:
        return dict(_sessions)
