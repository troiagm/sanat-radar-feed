"""sources.yaml ile yonetilen genel amacli kazi(yi)ci.

Her kaynak icin:
  name: kaynak adi
  city / lat / lng: etkinliklerin sehri ve merkez koordinati
  url: liste sayfasi
  item: etkinlik linklerini secen CSS secicisi (a etiketleri)
  base: goreli linkler icin taban URL (opsiyonel)
  category: varsayilan kategori (opsiyonel; yoksa basliktan tahmin edilir)
  max_detail: tarih bulmak icin kac detay sayfasi acilsin (vars. 12)

Detay sayfalarindan Turkce tarihler ("11 Ekim 2026", "30 Agustos'a kadar")
regex ile cekilir; bulunamazsa etkinlik tarihsiz kalir (uygulama listenin
sonunda gosterir).
"""
import hashlib
import re
import time
from datetime import datetime, timedelta
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

MONTHS = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5,
    "mayis": 5, "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8,
    "eylül": 9, "eylul": 9, "ekim": 10, "kasım": 11, "kasim": 11,
    "aralık": 12, "aralik": 12,
}
DATE_RE = re.compile(
    r"(\d{1,2})\s+(Ocak|Şubat|Subat|Mart|Nisan|Mayıs|Mayis|Haziran|Temmuz|"
    r"Ağustos|Agustos|Eylül|Eylul|Ekim|Kasım|Kasim|Aralık|Aralik)"
    r"(?:\s+(\d{4}))?",
    re.IGNORECASE,
)

KEYWORD_CATEGORIES = [
    ("atolye", ["atölye", "atolye", "workshop", "kurs"]),
    ("sergi", ["sergi", "sergisi", "bienal"]),
    ("konser", ["konser", "konseri", "resital", "dinleti"]),
    ("tiyatro", ["tiyatro", "oyunu", "sahneleniyor"]),
    ("dans", ["dans", "bale"]),
    ("film", ["film", "gösterim", "gosterim", "sinema"]),
]


def guess_category(text: str, default: str | None) -> str:
    t = text.lower()
    for cat, words in KEYWORD_CATEGORIES:
        if any(w in t for w in words):
            return cat
    return default or "diger"


def extract_date(text: str):
    """Metindeki ilk mantikli (gecmis olmayan) tarihi ISO olarak dondurur."""
    now = datetime.now()
    candidates = []
    for m in DATE_RE.finditer(text):
        day = int(m.group(1))
        month = MONTHS.get(m.group(2).lower())
        if not month or not (1 <= day <= 31):
            continue
        year = int(m.group(3)) if m.group(3) else now.year
        if not m.group(3) and month < now.month - 1:
            year += 1  # yilsiz ve gecmis gorunen ay -> gelecek yil varsay
        try:
            d = datetime(year, month, day)
        except ValueError:
            continue
        if now - timedelta(days=2) <= d <= now + timedelta(days=400):
            candidates.append(d)
    if not candidates:
        return None
    return min(candidates).strftime("%Y-%m-%dT12:00:00")


def scrape(src: dict):
    url = src["url"]
    base = src.get("base") or url
    r = requests.get(url, headers=HEADERS, timeout=40)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    links = soup.select(src["item"])
    seen, items = set(), []
    for a in links:
        href = a.get("href") or ""
        title = " ".join(a.get_text(" ", strip=True).split())
        if not href or len(title) < 8:
            continue
        full = urljoin(base, href)
        if full in seen:
            continue
        seen.add(full)
        items.append((title, full))

    events = []
    max_detail = int(src.get("max_detail", 12))
    for i, (title, link) in enumerate(items[:40]):
        date = None
        if i < max_detail:
            try:
                dr = requests.get(link, headers=HEADERS, timeout=20)
                if dr.ok:
                    dtext = BeautifulSoup(dr.text, "html.parser").get_text(" ")
                    date = extract_date(dtext)
                time.sleep(0.5)  # kibar kazima
            except Exception:  # noqa: BLE001
                pass

        uid = hashlib.md5((src["name"] + title).encode()).hexdigest()[:12]
        events.append({
            "id": f"src_{uid}",
            "name": title[:140],
            "date": date,
            "city": src.get("city", ""),
            "venue": src.get("venue", src["name"]),
            "lat": src.get("lat"),
            "lng": src.get("lng"),
            "category": guess_category(title, src.get("category")),
            "url": link,
            "image": None,
            "price_min": None,
            "price_max": None,
            "currency": None,
            "source": src["name"],
        })
    return events
