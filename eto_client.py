from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple
from xml.etree import ElementTree

import httpx

from config import settings


_COUNTRY_CACHE: Tuple[float, Dict[str, int]] = (0.0, {})
_DEPARTURE_CACHE: Tuple[float, Dict[str, int]] = (0.0, {})
_MEAL_CACHE: Tuple[float, Dict[int, str]] = (0.0, {})
_ROOM_CACHE: Tuple[float, Dict[int, str]] = (0.0, {})
_OP_CACHE: Tuple[float, Dict[int, str]] = (0.0, {})
_HOTEL_CACHE: Dict[int, Tuple[float, Dict[int, str]]] = {}
_LAST_AUTH: Dict[str, str] = {}
_COUNTRY_FALLBACK = {
    "египет": 1,
    "турция": 4,
    "оаэ": 9,
    "таиланд": 2,
    "кипр": 15,
    "греция": 6,
    "испания": 14,
    "италия": 24,
    "франция": 32,
    "мальдивы": 8,
    "вьетнам": 16,
    "индонезия": 7,
    "доминикана": 11,
    "куба": 10,
    "тунис": 5,
}
_DEPARTURE_FALLBACK = {
    "москва": 1,
    "санкт-петербург": 5,
    "спб": 5,
    "питер": 5,
    "казань": 10,
    "екатеринбург": 3,
    "новосибирск": 9,
    "минск": 57,
    "алматы": 60,
    "астана": 59,
}


def _extract_request_id(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        if "result" in payload and isinstance(payload["result"], dict):
            rid = payload["result"].get("requestid")
            if rid:
                return str(rid)
        for k in [k.strip() for k in settings.search_id_keys.split(",") if k.strip()]:
            if k in payload and payload[k]:
                return str(payload[k])
    return None


def _request(url: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if not url:
        return {"success": False, "error": "URL не задан. Укажи MODSEARCH_URL/MODRESULT_URL"}

    try:
        with httpx.Client(timeout=settings.request_timeout) as client:
            r = client.get(url, params=params, headers=settings.headers)
            r.raise_for_status()
            try:
                data = r.json()
            except Exception:
                data = {"raw_text": r.text}
            return {"success": True, "data": data}
    except httpx.HTTPError as e:
        return {"success": False, "error": str(e)}


def _fetch_list(url: str, key_name: str, id_field: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    if not url:
        return {}
    try:
        with httpx.Client(timeout=settings.request_timeout) as client:
            r = client.get(url, headers=settings.headers, params=params or {})
            r.raise_for_status()
            text = r.text or ""
    except httpx.HTTPError:
        return {}

    # JSON
    try:
        data = r.json()
        if isinstance(data, dict):
            items = data.get(key_name)
            if isinstance(items, list):
                out: Dict[str, int] = {}
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("name")
                    _id = item.get(id_field) or item.get("id")
                    if not name or _id is None:
                        continue
                    out[str(name).strip().lower()] = int(_id)
                return out
    except Exception:
        pass

    # XML fallback
    try:
        root = ElementTree.fromstring(text)
        out: Dict[str, int] = {}
        for node in root.findall(f".//{key_name}"):
            name = node.findtext("name")
            _id = node.findtext(id_field) or node.findtext("id")
            if not name or not _id:
                continue
            out[str(name).strip().lower()] = int(_id)
        return out
    except Exception:
        return {}




def _get_country_ids() -> Dict[str, int]:
    global _COUNTRY_CACHE
    ts, cached = _COUNTRY_CACHE
    if time.time() - ts < settings.list_cache_ttl and cached:
        return cached
    data = _fetch_list(settings.listcountry_url, "country", "id")
    if not data:
        data = dict(_COUNTRY_FALLBACK)
    _COUNTRY_CACHE = (time.time(), data)
    return data


def _get_departure_ids() -> Dict[str, int]:
    global _DEPARTURE_CACHE
    ts, cached = _DEPARTURE_CACHE
    if time.time() - ts < settings.list_cache_ttl and cached:
        return cached
    data = _fetch_list(settings.listdep_url, "departure", "id")
    if not data:
        data = dict(_DEPARTURE_FALLBACK)
    _DEPARTURE_CACHE = (time.time(), data)
    return data


def _get_meal_names() -> Dict[int, str]:
    global _MEAL_CACHE
    ts, cached = _MEAL_CACHE
    if time.time() - ts < settings.list_cache_ttl and cached:
        return cached
    raw = _fetch_list(settings.listmeal_url, "meal", "id")
    out: Dict[int, str] = {}
    for name, _id in raw.items():
        try:
            out[int(_id)] = name
        except Exception:
            continue
    _MEAL_CACHE = (time.time(), out)
    return out


def _get_room_names() -> Dict[int, str]:
    global _ROOM_CACHE
    ts, cached = _ROOM_CACHE
    if time.time() - ts < settings.list_cache_ttl and cached:
        return cached
    raw = _fetch_list(settings.listroom_url, "room", "id")
    out: Dict[int, str] = {}
    for name, _id in raw.items():
        try:
            out[int(_id)] = name
        except Exception:
            continue
    _ROOM_CACHE = (time.time(), out)
    return out


def _get_operator_names() -> Dict[int, str]:
    global _OP_CACHE
    ts, cached = _OP_CACHE
    if time.time() - ts < settings.list_cache_ttl and cached:
        return cached
    raw = _fetch_list(settings.listoperator_url, "operator", "id")
    out: Dict[int, str] = {}
    for name, _id in raw.items():
        try:
            out[int(_id)] = name
        except Exception:
            continue
    _OP_CACHE = (time.time(), out)
    return out


def _get_hotel_names(country_id: Optional[int], session: Optional[str], referrer: Optional[str], force_refresh: bool = False) -> Dict[int, str]:
    if not country_id:
        return {}
    if not force_refresh:
        cached = _HOTEL_CACHE.get(country_id)
        if cached:
            ts, data = cached
            if time.time() - ts < settings.list_cache_ttl and data:
                return data
    out: Dict[int, str] = {}

    # 1) listdev.php (allhotel)
    listdev_params = {
        "type": "allhotel",
        "hotcountry": country_id,
        "format": "json",
    }
    if referrer or settings.default_referrer:
        listdev_params["referrer"] = referrer or settings.default_referrer
    if session or settings.default_session:
        listdev_params["session"] = session or settings.default_session
    resp = _request(settings.listdev_url, listdev_params)
    if resp.get("success"):
        data = resp.get("data")
        if isinstance(data, dict) and "raw_text" in data:
            try:
                import json as _json
                data = _json.loads(data.get("raw_text") or "{}")
            except Exception:
                data = {}
        if isinstance(data, dict):
            payload = data
            if isinstance(payload.get("data"), dict):
                payload = payload.get("data") or payload
            if isinstance(payload.get("result"), dict):
                payload = payload.get("result") or payload

            # listdev.php format: {"lists":{"hotels":{"hotel":[...]}}}
            if isinstance(payload.get("lists"), dict):
                lists = payload.get("lists") or {}
                hotels = None
                if isinstance(lists.get("hotels"), dict):
                    hotels = (lists.get("hotels") or {}).get("hotel")
                if hotels is None:
                    hotels = (lists.get("hotel") if isinstance(lists.get("hotel"), list) else None)
            else:
                hotels = payload.get("hotel") or payload.get("hotels") or payload.get("items")
            if isinstance(hotels, list):
                for h in hotels:
                    if not isinstance(h, dict):
                        continue
                    hid = h.get("id") or h.get("hotelid")
                    name = h.get("name")
                    if hid is None or not name:
                        continue
                    try:
                        out[int(hid)] = str(name)
                    except Exception:
                        continue
            elif isinstance(hotels, dict):
                for hid, h in hotels.items():
                    if not isinstance(h, dict):
                        continue
                    name = h.get("name")
                    if not name:
                        continue
                    try:
                        out[int(hid)] = str(name)
                    except Exception:
                        continue

            # If hotels are top-level numeric keys
            if not out:
                for k, v in payload.items():
                    if not isinstance(k, str) or not k.isdigit():
                        continue
                    if not isinstance(v, dict) or "name" not in v:
                        continue
                    try:
                        out[int(k)] = str(v.get("name"))
                    except Exception:
                        continue

    # 2) listhotel.php fallback
    if not out:
        raw = _fetch_list(settings.listhotel_url, "hotel", "id", params={"country": country_id})
        for name, _id in raw.items():
            try:
                out[int(_id)] = name
            except Exception:
                continue

    _HOTEL_CACHE[country_id] = (time.time(), out)
    return out


def _normalize_date(value: Any) -> Any:
    if value is None:
        return value
    s = str(value).strip()
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return f"{s[8:10]}.{s[5:7]}.{s[0:4]}"
    return s


def _normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = payload.copy()
    data.pop("limit", None)
    data.pop("max", None)

    if "datefrom" not in data:
        if "date_from" in data:
            data["datefrom"] = _normalize_date(data.pop("date_from"))
        elif "s_j_date_from" in data:
            data["datefrom"] = _normalize_date(data.pop("s_j_date_from"))
    if "dateto" not in data:
        if "date_to" in data:
            data["dateto"] = _normalize_date(data.pop("date_to"))
        elif "s_j_date_to" in data:
            data["dateto"] = _normalize_date(data.pop("s_j_date_to"))

    if "nights" in data and "nightsfrom" not in data and "nightsto" not in data:
        nights = data.pop("nights")
        data["nightsfrom"] = nights
        data["nightsto"] = nights
    if "nights_from" in data and "nightsfrom" not in data:
        data["nightsfrom"] = data.pop("nights_from")
    if "nights_to" in data and "nightsto" not in data:
        data["nightsto"] = data.pop("nights_to")
    if "s_nights_from" in data and "nightsfrom" not in data:
        data["nightsfrom"] = data.pop("s_nights_from")
    if "s_nights_to" in data and "nightsto" not in data:
        data["nightsto"] = data.pop("s_nights_to")

    if "country" in data:
        val = data.pop("country")
        if isinstance(val, str):
            key = val.strip().lower()
            val = _get_country_ids().get(key)
            if val is None:
                data["__country_error"] = f"Страна '{key}' не найдена в базе Tourvisor"
            else:
                data["country"] = int(val)
        else:
            data["country"] = val
    elif "s_country" in data:
        data["country"] = data.pop("s_country")

    if "city_from" in data:
        val = data.pop("city_from")
        if isinstance(val, str):
            key = val.strip().lower()
            val = _get_departure_ids().get(key, val)
            if isinstance(val, str) and val.isdigit():
                val = int(val)
        data["departure"] = val
    elif "s_flyfrom" in data:
        data["departure"] = data.pop("s_flyfrom")

    if "adults" in data:
        data["adults"] = data.pop("adults")
    elif "s_adults" in data:
        data["adults"] = data.pop("s_adults")

    if settings.default_referrer and "referrer" not in data:
        data["referrer"] = settings.default_referrer
    if settings.default_session and "session" not in data:
        data["session"] = settings.default_session

    data.setdefault("regular", 1)
    data.setdefault("child", 0)
    data.setdefault("meal", 0)
    data.setdefault("rating", 0)
    data.setdefault("pricefrom", 0)
    data.setdefault("priceto", 0)
    data.setdefault("currency", 0)
    data.setdefault("formmode", 0)
    data.setdefault("pricetype", 0)

    return data


def search_tours(payload: Dict[str, Any]) -> Dict[str, Any]:
    """modsearch -> poll modresult 1-3 раза -> вернуть нормализованные туры."""
    normalized = _normalize_payload(payload or {})
    limit = int(payload.get("limit") or payload.get("max") or settings.max_tours)
    unique_hotels = payload.get("unique_hotels", True)
    refresh_hotels = bool(payload.get("refresh_hotels"))
    country_id = normalized.get("country")
    if normalized.get("__country_error"):
        return {"success": False, "error": normalized.get("__country_error")}
    if normalized.get("session"):
        _LAST_AUTH["session"] = str(normalized.get("session"))
    if normalized.get("referrer"):
        _LAST_AUTH["referrer"] = str(normalized.get("referrer"))

    request_id = payload.get("requestid") or payload.get("request_id")
    if request_id:
        request_id = str(request_id)
    else:
        start = modsearch(normalized)
        if not start.get("success"):
            return start

        request_id = _extract_request_id(start.get("data"))
        if not request_id:
            return {
                "success": False,
                "error": "По этому направлению сейчас нет пакетных туров",
            }

    last: Optional[Dict[str, Any]] = None
    saw_block = False
    for _ in range(settings.poll_attempts):
        last = modresult(request_id)
        if last.get("success"):
            data = last.get("data")
            if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
                if "block" in data["data"]:
                    saw_block = True
                    if _has_tour_data(data):
                        tours = _normalize_result(
                            data,
                            country_id=country_id,
                            session=_LAST_AUTH.get("session"),
                            referrer=_LAST_AUTH.get("referrer"),
                            refresh_hotels=refresh_hotels,
                        )
                        if unique_hotels:
                            tours = _unique_hotels(tours)
                        if limit > 0:
                            tours = tours[:limit]
                        return {"success": True, "requestid": request_id, "tours": tours}
            if isinstance(data, dict) and "block" in data:
                saw_block = True
                if _has_tour_data(data):
                    tours = _normalize_result(
                        data,
                        country_id=country_id,
                        session=_LAST_AUTH.get("session"),
                        referrer=_LAST_AUTH.get("referrer"),
                        refresh_hotels=refresh_hotels,
                    )
                    if unique_hotels:
                        tours = _unique_hotels(tours)
                    if limit > 0:
                        tours = tours[:limit]
                    return {"success": True, "requestid": request_id, "tours": tours}
        time.sleep(settings.poll_interval)

    return {
        "success": False,
        "error": "Туры с ценами ещё не готовы" if saw_block else "data.block не появился",
        "requestid": request_id,
    }


def modsearch(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _request(settings.modsearch_url, payload)


def modresult(request_id: str) -> Dict[str, Any]:
    return _request(settings.modresult_url, {settings.result_id_param: request_id})


def _has_tour_data(raw: Dict[str, Any]) -> bool:
    data = raw.get("data", raw)
    if not isinstance(data, dict):
        return False
    block = data.get("block")
    if not isinstance(block, list):
        return False
    for b in block:
        hotels = b.get("hotel") if isinstance(b, dict) else None
        if hotels is None:
            continue
        if isinstance(hotels, dict):
            hotels = [hotels]
        if not isinstance(hotels, list):
            continue
        for h in hotels:
            tours = h.get("tour") if isinstance(h, dict) else None
            if tours is None:
                continue
            if isinstance(tours, dict):
                tours = [tours]
            if not isinstance(tours, list):
                continue
            for t in tours:
                if isinstance(t, dict) and (
                    _to_int(t.get("price")) or _to_int(t.get("pr"))
                ):
                    return True
    return False


def _normalize_result(
    raw: Dict[str, Any],
    country_id: Optional[int],
    session: Optional[str],
    referrer: Optional[str],
    refresh_hotels: bool = False,
) -> list[Dict[str, Any]]:
    data = raw.get("data", raw)
    if not isinstance(data, dict):
        return []

    block = data.get("block")
    if not isinstance(block, list):
        return []

    # Prefer in-response dictionaries (they often contain full names)
    hotel_dict: Dict[str, Any] = {}
    if isinstance(data.get("hotels"), dict):
        hotel_dict = data.get("hotels") or {}
    elif isinstance(data.get("hotel"), dict):
        maybe = data.get("hotel") or {}
        if all(isinstance(v, dict) for v in maybe.values()):
            hotel_dict = maybe

    if not hotel_dict:
        # Try treating top-level dict as hotels map: keep only numeric keys with hotel-like fields
        filtered: Dict[str, Any] = {}
        for k, v in data.items():
            if not isinstance(k, str) or not k.isdigit():
                continue
            if not isinstance(v, dict) or "name" not in v:
                continue
            if "countrycode" in v or "stars" in v or "region" in v or "link" in v:
                filtered[k] = v
        if filtered:
            hotel_dict = filtered

    room_dict = data.get("rooms") if isinstance(data.get("rooms"), dict) else {}
    meal_dict = data.get("meal") if isinstance(data.get("meal"), dict) else {}

    op_dict: Dict[int, str] = {}
    ops = data.get("operators")
    if isinstance(ops, list):
        for o in ops:
            if isinstance(o, dict) and o.get("id") is not None:
                try:
                    op_dict[int(o["id"])] = str(o.get("name") or "").strip() or None
                except Exception:
                    continue

    # Fallback to list endpoints if needed
    hotel_names = _get_hotel_names(
        country_id, session=session, referrer=referrer, force_refresh=refresh_hotels
    ) if not hotel_dict else {}
    meal_names = _get_meal_names() if not meal_dict else {}
    room_names = _get_room_names() if not room_dict else {}
    op_names = _get_operator_names() if not op_dict else {}

    tours: list[Dict[str, Any]] = []
    for b in block:
        hotels = b.get("hotel") if isinstance(b, dict) else None
        if hotels is None:
            continue
        if isinstance(hotels, dict):
            hotels = [hotels]
        if not isinstance(hotels, list):
            continue
        for h in hotels:
            if not isinstance(h, dict):
                continue
            hotel_id = h.get("hotelid") or h.get("id")
            tours_list = h.get("tour")
            if tours_list is None:
                continue
            if isinstance(tours_list, dict):
                tours_list = [tours_list]
            if not isinstance(tours_list, list):
                continue
            for t in tours_list:
                if not isinstance(t, dict):
                    continue
                price = _to_int(t.get("price") or t.get("pr"))
                if price is None:
                    continue
                tours.append(
                    {
                        "hotel_id": _to_int(hotel_id),
                        "hotel_name": (
                            (hotel_dict.get(str(hotel_id)) or {}).get("name")
                            if hotel_dict and hotel_id is not None
                            else (hotel_names.get(_to_int(hotel_id)) or f"Hotel {hotel_id}") if _to_int(hotel_id) else None
                        ),
                        "hotel": (
                            (hotel_dict.get(str(hotel_id)) or {}).get("name")
                            if hotel_dict and hotel_id is not None
                            else (hotel_names.get(_to_int(hotel_id)) or f"Hotel {hotel_id}") if _to_int(hotel_id) else f"Hotel {hotel_id}"
                        ),
                        "hotel_link": (
                            settings.hotel_link_base + str((hotel_dict.get(str(hotel_id)) or {}).get("link"))
                            if hotel_dict and hotel_id is not None and (hotel_dict.get(str(hotel_id)) or {}).get("link")
                            else None
                        ),
                        "operator": _to_int(t.get("operator") or t.get("op")),
                        "operator_name": (
                            op_dict.get(_to_int(t.get("operator") or t.get("op")))
                            if _to_int(t.get("operator") or t.get("op")) is not None
                            else op_names.get(_to_int(t.get("operator") or t.get("op")))
                        ),
                        "date": _to_date(t.get("date") or t.get("dt")),
                        "nights": _to_int(t.get("nights") or t.get("nt")),
                        "price": price,
                        "room": _to_int(t.get("room") or t.get("rm")),
                        "room_name": (
                            (room_dict.get(str(_to_int(t.get("room") or t.get("rm")))) or {}).get("name")
                            if room_dict and _to_int(t.get("room") or t.get("rm")) is not None
                            else room_names.get(_to_int(t.get("room") or t.get("rm")))
                        ),
                        "meal": _to_int(t.get("meal") or t.get("ml")),
                        "meal_name": (
                            (meal_dict.get(str(_to_int(t.get("meal") or t.get("ml")))) or {}).get("name")
                            if meal_dict and _to_int(t.get("meal") or t.get("ml")) is not None
                            else meal_names.get(_to_int(t.get("meal") or t.get("ml")))
                        ),
                    }
                )
    return tours


def _unique_hotels(tours: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Группирует туры по отелю и оставляет самый дешевый вариант."""
    best: Dict[int, Dict[str, Any]] = {}
    for t in tours:
        hid = t.get("hotel_id")
        if hid is None:
            continue
        prev = best.get(hid)
        if not prev or (t.get("price") or 0) < (prev.get("price") or 0):
            best[hid] = t
    return list(best.values())


def _to_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except Exception:
        return None


def _to_date(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return s
    if len(s) >= 10 and s[4] == "." and s[7] == ".":
        return f"{s[6:10]}-{s[3:5]}-{s[0:2]}"
    return s or None
