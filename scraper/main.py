"""SanatRadar feed uretici — v2 (sehir bazli dosyalar).

Cikti:
  docs/feed.json            -> tum etkinlikler (yedek)
  docs/cities/<il>.json     -> il bazinda kucuk dosyalar (uygulama bunu ceker)

Her etkinlik, koordinatina gore en yakin il merkezine atanir;
koordinati yoksa 'city' alani il adiyla eslestirilir.
"""
import json
import math
import os
import sys
from datetime import datetime, timezone

import yaml

sys.path.insert(0, os.path.dirname(__file__))
import ticketmaster  # noqa: E402
import generic  # noqa: E402

HERE = os.path.dirname(__file__)
DOCS = os.path.join(HERE, "..", "docs")

PROVINCES = {
    "Adana": (37.00, 35.32), "Adıyaman": (37.76, 38.28),
    "Afyonkarahisar": (38.76, 30.54), "Ağrı": (39.72, 43.05),
    "Aksaray": (38.37, 34.03), "Amasya": (40.65, 35.83),
    "Ankara": (39.93, 32.86), "Antalya": (36.90, 30.70),
    "Ardahan": (41.11, 42.70), "Artvin": (41.18, 41.82),
    "Aydın": (37.84, 27.84), "Balıkesir": (39.65, 27.89),
    "Bartın": (41.64, 32.34), "Batman": (37.88, 41.13),
    "Bayburt": (40.26, 40.22), "Bilecik": (40.15, 29.98),
    "Bingöl": (38.88, 40.50), "Bitlis": (38.40, 42.11),
    "Bolu": (40.74, 31.61), "Burdur": (37.72, 30.29),
    "Bursa": (40.19, 29.06), "Çanakkale": (40.15, 26.41),
    "Çankırı": (40.60, 33.62), "Çorum": (40.55, 34.95),
    "Denizli": (37.78, 29.09), "Diyarbakır": (37.91, 40.24),
    "Düzce": (40.84, 31.16), "Edirne": (41.68, 26.56),
    "Elazığ": (38.68, 39.22), "Erzincan": (39.75, 39.49),
    "Erzurum": (39.90, 41.27), "Eskişehir": (39.78, 30.52),
    "Gaziantep": (37.07, 37.38), "Giresun": (40.91, 38.39),
    "Gümüşhane": (40.46, 39.48), "Hakkari": (37.58, 43.74),
    "Hatay": (36.20, 36.16), "Iğdır": (39.92, 44.04),
    "Isparta": (37.76, 30.55), "İstanbul": (41.01, 28.98),
    "İzmir": (38.42, 27.14), "Kahramanmaraş": (37.58, 36.93),
    "Karabük": (41.20, 32.62), "Karaman": (37.18, 33.22),
    "Kars": (40.60, 43.10), "Kastamonu": (41.38, 33.78),
    "Kayseri": (38.73, 35.48), "Kırıkkale": (39.85, 33.51),
    "Kırklareli": (41.73, 27.22), "Kırşehir": (39.15, 34.16),
    "Kilis": (36.72, 37.12), "Kocaeli": (40.85, 29.88),
    "Konya": (37.87, 32.48), "Kütahya": (39.42, 29.99),
    "Malatya": (38.35, 38.31), "Manisa": (38.61, 27.43),
    "Mardin": (37.31, 40.74), "Mersin": (36.81, 34.63),
    "Muğla": (37.22, 28.36), "Muş": (38.73, 41.49),
    "Nevşehir": (38.62, 34.71), "Niğde": (37.97, 34.68),
    "Ordu": (40.98, 37.88), "Osmaniye": (37.07, 36.25),
    "Rize": (41.02, 40.52), "Sakarya": (40.77, 30.40),
    "Samsun": (41.29, 36.33), "Siirt": (37.93, 41.94),
    "Sinop": (42.03, 35.15), "Sivas": (39.75, 37.02),
    "Şanlıurfa": (37.16, 38.79), "Şırnak": (37.52, 42.46),
    "Tekirdağ": (40.98, 27.51), "Tokat": (40.31, 36.55),
    "Trabzon": (41.00, 39.72), "Tunceli": (39.11, 39.55),
    "Uşak": (38.68, 29.41), "Van": (38.49, 43.38),
    "Yalova": (40.65, 29.27), "Yozgat": (39.82, 34.81),
    "Zonguldak": (41.45, 31.79),
}

TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜâÂ", "cgiosuCGIOSUaA")


def slug(name: str) -> str:
    s = name.translate(TR_MAP).lower()
    return "".join(ch for ch in s if ch.isalnum())


SLUG_TO_PROVINCE = {slug(p): p for p in PROVINCES}


def nearest_province(lat, lng):
    best, best_d = None, 1e9
    for name, (plat, plng) in PROVINCES.items():
        d = (plat - lat) ** 2 + ((plng - lng) * math.cos(math.radians(lat))) ** 2
        if d < best_d:
            best, best_d = name, d
    return best


def assign_province(e):
    if e.get("lat") is not None and e.get("lng") is not None:
        return nearest_province(e["lat"], e["lng"])
    return SLUG_TO_PROVINCE.get(slug(e.get("city", "") or ""))


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))


def main():
    events = []
    stats = {}

    api_key = os.environ.get("TM_API_KEY", "").strip()
    if api_key:
        try:
            tm_events = ticketmaster.fetch_turkey(api_key)
            events.extend(tm_events)
            stats["ticketmaster"] = len(tm_events)
        except Exception as e:  # noqa: BLE001
            print(f"[HATA] ticketmaster: {e}")
            stats["ticketmaster"] = f"HATA: {e}"
    else:
        print("[UYARI] TM_API_KEY tanimli degil, Ticketmaster atlandi")
        stats["ticketmaster"] = "anahtar yok"

    with open(os.path.join(HERE, "sources.yaml"), encoding="utf-8") as f:
        sources = yaml.safe_load(f) or []
    for src in sources:
        name = src.get("name", "?")
        try:
            found = generic.scrape(src)
            events.extend(found)
            stats[name] = len(found)
            print(f"[OK] {name}: {len(found)} etkinlik")
        except Exception as e:  # noqa: BLE001
            print(f"[HATA] {name}: {e}")
            stats[name] = f"HATA: {e}"

    by_id = {e["id"]: e for e in events}
    merged = sorted(by_id.values(), key=lambda e: e.get("date") or "9999")

    now = datetime.now(timezone.utc).isoformat()

    # 1) Tam feed (yedek)
    dump(os.path.join(DOCS, "feed.json"),
         {"generated_at": now, "stats": stats, "events": merged})

    # 2) Il bazli kucuk dosyalar
    by_city = {}
    unassigned = 0
    for e in merged:
        prov = assign_province(e)
        if prov is None:
            unassigned += 1
            continue
        by_city.setdefault(prov, []).append(e)

    for prov, evs in by_city.items():
        dump(os.path.join(DOCS, "cities", f"{slug(prov)}.json"),
             {"generated_at": now, "city": prov, "events": evs})

    print("\n--- OZET ---")
    for k, v in stats.items():
        print(f"{k}: {v}")
    print(f"TOPLAM (tekil): {len(merged)}, il dosyasi: {len(by_city)}, "
          f"atanamayan: {unassigned}")
    for prov in sorted(by_city, key=lambda p: -len(by_city[p]))[:10]:
        print(f"  {prov}: {len(by_city[prov])}")


if __name__ == "__main__":
    main()
