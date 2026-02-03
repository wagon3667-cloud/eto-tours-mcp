import json
import os
from dataclasses import dataclass, field
from typing import Dict, Optional


def _json_env(name: str, default: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    raw = os.environ.get(name)
    if not raw:
        return default or {}
    try:
        return json.loads(raw)
    except Exception:
        return default or {}


@dataclass(frozen=True)
class Settings:
    modsearch_url: str = os.environ.get("MODSEARCH_URL", "").strip()
    modresult_url: str = os.environ.get("MODRESULT_URL", "").strip()
    listcountry_url: str = os.environ.get("LISTCOUNTRY_URL", "https://tourvisor.ru/xml/listcountry.php").strip()
    listdep_url: str = os.environ.get("LISTDEP_URL", "https://tourvisor.ru/xml/listdep.php").strip()
    listhotel_url: str = os.environ.get("LISTHOTEL_URL", "https://tourvisor.ru/xml/listhotel.php").strip()
    listmeal_url: str = os.environ.get("LISTMEAL_URL", "https://tourvisor.ru/xml/listmeal.php").strip()
    listroom_url: str = os.environ.get("LISTROOM_URL", "https://tourvisor.ru/xml/listroom.php").strip()
    listoperator_url: str = os.environ.get("LISTOPERATOR_URL", "https://tourvisor.ru/xml/listoperator.php").strip()
    hotel_link_base: str = os.environ.get("HOTEL_LINK_BASE", "https://tourvisor.ru/countries#!/hotel=").strip()
    listdev_url: str = os.environ.get("LISTDEV_URL", "https://tourvisor.ru/xml/listdev.php").strip()
    headers: Dict[str, str] = field(default_factory=lambda: _json_env("ETO_HEADERS_JSON", {}))
    default_referrer: str = os.environ.get("DEFAULT_REFERRER", "").strip()
    default_session: str = os.environ.get("DEFAULT_SESSION", "").strip()
    result_id_param: str = os.environ.get("RESULT_ID_PARAM", "requestid")
    search_id_keys: str = os.environ.get("SEARCH_ID_KEYS", "requestid,request_id,search_id,id,uid")
    request_timeout: int = int(os.environ.get("REQUEST_TIMEOUT", "30"))
    poll_interval: float = float(os.environ.get("POLL_INTERVAL", "2.0"))
    poll_attempts: int = int(os.environ.get("POLL_ATTEMPTS", "25"))
    max_tours: int = int(os.environ.get("MAX_TOURS", "20"))
    list_cache_ttl: int = int(os.environ.get("LIST_CACHE_TTL", "21600"))


settings = Settings()
