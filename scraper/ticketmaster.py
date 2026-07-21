"""Ticketmaster Discovery API: Turkiye'deki tum etkinlikler (spor haric)."""
import time

import requests

URL = "https://app.ticketmaster.com/discovery/v2/events.json"


def _category(segment: str, genre: str) -> str:
    s, g = segment.lower(), genre.lower()
    if "music" in s:
        return "konser"
    if "film" in s:
        return "film"
    if "arts" in s or "theatre" in s:
        if "theatre" in g or "theater" in g:
            return "tiyatro"
        if "dance" in g or "ballet" in g:
            return "dans"
        if "fine art" in g:
            return "sergi"
        return "sahne"
    return "diger"


def fetch_turkey(api_key: str):
    events = []
    for page in range(5):  # 5 x 200 = 1000 (API'nin derin sayfalama siniri)
        r = requests.get(
            URL,
            params={
                "apikey": api_key,
                "countryCode": "TR",
                "locale": "*",
                "size": "200",
                "page": str(page),
                "sort": "date,asc",
            },
            timeout=30,
        )
        if r.status_code != 200:
            break
        data = r.json()
        items = (data.get("_embedded") or {}).get("events") or []
        if not items:
            break
        for e in items:
            ev = _parse(e)
            if ev:
                events.append(ev)
        if len(items) < 200:
            break
        time.sleep(0.6)  # saniyede 2 istek limitine saygi
    return events


def _parse(e):
    try:
        cls = (e.get("classifications") or [{}])[0]
        segment = ((cls.get("segment") or {}).get("name")) or ""
        genre = ((cls.get("genre") or {}).get("name")) or ""
        if "sport" in segment.lower():
            return None

        start = (e.get("dates") or {}).get("start") or {}
        date = None
        if start.get("localDate"):
            date = start["localDate"] + "T" + start.get("localTime", "20:00:00")

        venue = ((e.get("_embedded") or {}).get("venues") or [{}])[0]
        loc = venue.get("location") or {}
        city = ((venue.get("city") or {}).get("name")) or ""

        image, best_w = None, 0
        for img in e.get("images") or []:
            w = img.get("width") or 0
            if w > best_w and img.get("url"):
                best_w, image = w, img["url"]

        price = (e.get("priceRanges") or [{}])[0]

        return {
            "id": "tm_" + e["id"],
            "name": e.get("name", ""),
            "date": date,
            "city": city,
            "venue": venue.get("name", ""),
            "lat": float(loc["latitude"]) if loc.get("latitude") else None,
            "lng": float(loc["longitude"]) if loc.get("longitude") else None,
            "category": _category(segment, genre),
            "url": e.get("url", ""),
            "image": image,
            "price_min": price.get("min"),
            "price_max": price.get("max"),
            "currency": price.get("currency"),
            "source": "ticketmaster",
        }
    except Exception:  # noqa: BLE001
        return None
