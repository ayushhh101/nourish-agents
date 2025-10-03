# restaurant_agent.py (refined Overpass-based, free)
import requests
from typing import Dict, List, Optional

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def _overpass_query(lat: float, lng: float, radius_m: int, cuisines: List[str]) -> str:
    # Build cuisine filter OR chain for regex match, e.g., indian|chinese|thai
    cuisine_filters = ""
    if cuisines:
        ors = "|".join(sorted({c.strip().lower() for c in cuisines if c}))
        # Match any of the cuisine terms if the cuisine tag exists
        cuisine_filters = f'[~"cuisine"~"{ors}"]'
    # Only return elements that have a name to avoid blank entries
    return f"""
[out:json][timeout:25];
(
  nwr["amenity"="restaurant"]["name"]{cuisine_filters}(around:{radius_m},{lat},{lng});
);
out center tags;
"""

def _normalize_overpass_elem(e: Dict) -> Optional[Dict]:
    tags = e.get("tags", {}) or {}
    name = (tags.get("name") or "").strip()
    if not name:
        return None
    cuisine = tags.get("cuisine")
    # Build address if available
    address = ", ".join([x for x in [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:city"),
        tags.get("addr:postcode"),
    ] if x])
    # Coordinates: use node lat/lon or way/relation center
    lat = e.get("lat")
    lng = e.get("lon")
    if lat is None or lng is None:
        center = e.get("center") or {}
        lat = center.get("lat")
        lng = center.get("lon")
    if lat is None or lng is None:
        return None

    # Types: split cuisine into a list if semicolon separated
    types = ["restaurant"]
    if cuisine:
        types.extend([t.strip() for t in str(cuisine).split(";") if t.strip()])

    return {
        "name": name,
        "address": address,
        "rating": None,
        "price_level": None,
        "types": types,
        "id": str(e.get("id")),
        "lat": lat,
        "lng": lng,
        "source": "overpass_osm",
    }

def get_nearby_restaurants(lat: float, lng: float, cuisines: Optional[List[str]] = None, radius_m: int = 3000, limit: int = 30) -> Dict:
    q = _overpass_query(lat, lng, radius_m, cuisines or [])
    try:
        resp = requests.post(OVERPASS_URL, data={"data": q}, timeout=25)
        resp.raise_for_status()
        data = resp.json() or {}
        elements = data.get("elements", []) or []
        items = []
        for e in elements:
            if not isinstance(e, dict):
                continue
            n = _normalize_overpass_elem(e)
            if n:
                items.append(n)
        # Sort deterministically: by name
        items.sort(key=lambda x: x["name"].lower())
        return {"restaurants": items[:limit]}
    except Exception:
        return {"restaurants": []}
