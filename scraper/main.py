"""SanatRadar feed uretici.

Calisma sirasi:
1. Ticketmaster Discovery API'den Turkiye'deki tum sanat etkinlikleri
   (TM_API_KEY ortam degiskeni gerekli)
2. sources.yaml'daki web kaynaklarindan sergi/atolye etkinlikleri
3. Hepsi docs/feed.json'a yazilir; uygulama bu dosyayi okur.

Yerel test: TM_API_KEY=xxx python scraper/main.py
"""
import json
import os
import sys
from datetime import datetime, timezone

import yaml

sys.path.insert(0, os.path.dirname(__file__))
import ticketmaster  # noqa: E402
import generic  # noqa: E402

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "docs", "feed.json")


def main():
    events = []
    stats = {}

    # 1) Ticketmaster
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

    # 2) Web kaynaklari
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

    # 3) Tekle (id'ye gore) ve tarihe gore sirala
    by_id = {}
    for e in events:
        by_id[e["id"]] = e
    merged = sorted(
        by_id.values(),
        key=lambda e: e.get("date") or "9999",
    )

    feed = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": stats,
        "events": merged,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=1)

    print("\n--- OZET ---")
    for k, v in stats.items():
        print(f"{k}: {v}")
    print(f"TOPLAM (tekil): {len(merged)}")
    print(f"Yazildi: {OUT}")


if __name__ == "__main__":
    main()
