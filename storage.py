import threading
from typing import Any, Dict, Optional


class SearchStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._last_search_id: Optional[str] = None
        self._last_payload: Optional[Dict[str, Any]] = None

    def set_last(self, search_id: Optional[str], payload: Dict[str, Any]) -> None:
        with self._lock:
            self._last_search_id = search_id
            self._last_payload = payload

    def get_last_id(self) -> Optional[str]:
        with self._lock:
            return self._last_search_id

    def get_last_payload(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._last_payload


store = SearchStore()
