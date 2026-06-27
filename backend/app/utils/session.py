import uuid
import time
from typing import Optional
from app.schemas.policy import ExtractedPolicy

SESSION_TTL_SECONDS = 1800  # 30 minutes


class SessionStore:
    """In-memory session store. No persistence. No disk writes after extraction."""

    def __init__(self):
        self._store: dict[str, dict] = {}

    def create(self) -> str:
        session_id = str(uuid.uuid4())
        self._store[session_id] = {
            "policies": [],
            "created_at": time.time(),
        }
        return session_id

    def get_policies(self, session_id: str) -> Optional[list[ExtractedPolicy]]:
        self._evict_expired()
        session = self._store.get(session_id)
        return session["policies"] if session else None

    def set_policies(self, session_id: str, policies: list[ExtractedPolicy]) -> None:
        if session_id in self._store:
            self._store[session_id]["policies"] = policies

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    def _evict_expired(self) -> None:
        now = time.time()
        expired = [
            k for k, v in self._store.items()
            if now - v["created_at"] > SESSION_TTL_SECONDS
        ]
        for k in expired:
            del self._store[k]


session_store = SessionStore()  # singleton
