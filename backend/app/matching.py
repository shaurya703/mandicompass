"""Fuzzy mapping of free-text Agmarknet commodity/market names onto our ids.

Agmarknet spells things many ways ("Bengal Gram (Gram)(Whole)", "Tomato",
"Bangalore"); these helpers map them to the ids in commodities.json /
markets.json so the live fetcher and the dataset stay aligned.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _f(obj, field: str):
    """Read a field from either a raw dict (fetch path) or a Pydantic model."""
    return obj[field] if isinstance(obj, dict) else getattr(obj, field)


# Common Agmarknet aliases -> our commodity id.
_COMMODITY_ALIASES = {
    "paddy": "paddy", "paddydhancommon": "paddy", "rice": "paddy",
    "wheat": "wheat", "ragi": "ragi", "fingermillet": "ragi",
    "jowar": "jowar", "sorghum": "jowar", "bajra": "bajra", "pearlmillet": "bajra",
    "maize": "maize", "tur": "tur", "arhar": "tur", "redgram": "tur", "pigeonpea": "tur",
    "moong": "moong", "greengram": "moong", "urad": "urad", "blackgram": "urad",
    "gram": "gram", "bengalgram": "gram", "chana": "gram",
    "groundnut": "groundnut", "soybean": "soybean", "soyabean": "soybean",
    "sunflower": "sunflower", "mustard": "mustard", "rapeseed": "mustard",
    "cotton": "cotton", "tomato": "tomato", "onion": "onion", "potato": "potato",
}


def match_commodity(raw: str, commodities: list[dict]) -> str | None:
    n = _norm(raw)
    for alias, cid in _COMMODITY_ALIASES.items():
        if alias in n:
            return cid
    # fall back to direct id/name similarity
    best, score = None, 0.0
    for c in commodities:
        s = SequenceMatcher(None, n, _norm(_f(c, "name"))).ratio()
        if s > score:
            best, score = _f(c, "id"), s
    return best if score >= 0.6 else None


def match_market(raw_market: str, raw_district: str, markets: list[dict]) -> str | None:
    nm, nd = _norm(raw_market), _norm(raw_district)
    # exact-ish name or district contains
    for m in markets:
        if _norm(_f(m, "name")).startswith(nm[:6]) or (nm and nm in _norm(_f(m, "name"))):
            return _f(m, "id")
    for m in markets:
        if nd and nd in _norm(_f(m, "district")):
            return _f(m, "id")
    best, score = None, 0.0
    for m in markets:
        s = SequenceMatcher(None, nm, _norm(_f(m, "district"))).ratio()
        if s > score:
            best, score = _f(m, "id"), s
    return best if score >= 0.7 else None
