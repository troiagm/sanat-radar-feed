# SanatRadar Feed

Bu depo, SanatRadar uygulamasının etkinlik verisini günde 2 kez otomatik
üretir: Ticketmaster/Biletix (tüm Türkiye) + İstanbul, Ankara, İzmir ve
Bursa'nın sergi/atölye kaynakları → `docs/feed.json`.

Faydaları:
- Ticketmaster API anahtarı artık uygulamaya gömülmez (sadece burada,
  gizli değişken olarak durur) → anahtar çalınamaz, kota herkes için yetmez
  diye bir dert kalmaz (günde 2 çekim, sınırsız kullanıcı).
- Sergi ve atölyeler yapılandırılmış etkinlik olarak uygulamaya girer.
- Kaynak eklemek/düzeltmek için uygulamayı güncellemek gerekmez; sadece
  `scraper/sources.yaml` düzenlenir.

## Kurulum (bir kez, ~15 dakika)

1. **GitHub hesabı** yoksa github.com'dan aç (ücretsiz).
2. Sağ üstte **+ → New repository** → ad: `sanat-radar-feed` →
   **Public** seç → Create repository.
3. Bu klasördeki dosyaları yükle: repo sayfasında **uploading an existing
   file** linkine tıkla, bu klasörün İÇİNDEKİLERİ (`.github`, `scraper`,
   `docs`, `README.md`) sürükle-bırak → Commit changes.
   - Not: `.github` gizli klasördür; Windows'ta görünmüyorsa Dosya
     Gezgini'nde "Gizli öğeler"i aç. Sürükle-bırak klasörleri korumazsa
     "Add file → Create new file" ile `.github/workflows/build-feed.yml`
     yolunu elle yazıp içeriği yapıştırabilirsin.
4. **API anahtarını gizli değişken yap:** Repo → Settings → Secrets and
   variables → Actions → **New repository secret** →
   Name: `TM_API_KEY`, Secret: Ticketmaster Consumer Key'in → Add secret.
5. **İlk çalıştırma:** Repo → Actions sekmesi → soldan "Feed Guncelle" →
   sağda **Run workflow** → Run. 2-3 dakika sürer.
   - Yeşil ✓ görünce `docs/feed.json` oluşmuş demektir.
   - Çalıştırma logunda her kaynağın kaç etkinlik verdiği yazar
     ("OZET" bölümü). 0 veya HATA veren kaynak olursa logu Claude'a
     yapıştır; sources.yaml'daki seçiciyi birlikte düzeltiriz.
6. **Feed linkini al:** repo sayfasında `docs/feed.json` dosyasına tıkla →
   **Raw** düğmesi → tarayıcıdaki adresi kopyala. Şuna benzer:
   `https://raw.githubusercontent.com/KULLANICI_ADIN/sanat-radar-feed/main/docs/feed.json`
7. Bu linki uygulamada `lib/config.dart` → `feedUrl` değerine yapıştır.

Bundan sonrası otomatiktir: Actions her gün 07:00 ve 17:00'de (TR) feed'i
tazeler; uygulama her açılışta güncel dosyayı okur.

## Kaynak ekleme / düzeltme

`scraper/sources.yaml` içine yeni blok ekle (dosyada şablon ve açıklama
var), commit et, Actions'ı elle çalıştırıp logda sayıyı kontrol et.
Siteler tasarım değiştirirse tek yapman gereken buradaki `item`
seçicisini güncellemek — uygulama mağazada dokunulmadan kalır.

## Yerel test (istersen)

```
pip install -r scraper/requirements.txt
set TM_API_KEY=ANAHTARIN        (Windows)
python scraper/main.py
```
