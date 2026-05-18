# GamePulse 🎮

Gerçek zamanlı oyun fiyat ve indirim takip mikro servisi.  
**Stack:** Python 3.11+ · FastAPI · httpx · CheapShark API

---

## Proje Yapısı

```
gamepulse/
├── app/
│   ├── __init__.py      # Paket tanımlayıcı
│   ├── config.py        # Ortam değişkenleri ve sabitler
│   ├── main.py          # FastAPI uygulama giriş noktası
│   ├── routes.py        # HTTP endpoint tanımları
│   ├── schemas.py       # Pydantic request/response modelleri
│   └── services.py      # İş mantığı + CheapShark API istemcisi
├── .dockerignore        # Docker build context'ten hariç tutulan dosyalar
├── .env.example         # Ortam değişkenleri şablonu
├── Dockerfile           # Multi-stage production image tanımı
├── requirements.txt     # Python bağımlılıkları
└── README.md
```

---

## Kurulum ve Çalıştırma

### 1. Sanal ortam oluştur ve aktif et

```powershell
# Proje dizinine git
cd C:\Users\gurso\Desktop\gamepulse

# Sanal ortam oluştur
python -m venv venv

# Aktif et (Windows PowerShell)
.\venv\Scripts\Activate.ps1
```

> **Not:** Execution policy hatası alırsan şunu çalıştır:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### 2. Bağımlılıkları yükle

```powershell
pip install -r requirements.txt
```

### 3. Ortam değişkenlerini hazırla

```powershell
Copy-Item .env.example .env
```

### 4. Sunucuyu başlat

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

`--reload` bayrağı: Kod değişikliklerinde sunucu otomatik yeniden başlar (development için ideal).

---

## API Endpoint'leri

| Method | URL | Açıklama |
|--------|-----|----------|
| `GET` | `/status` | Sağlık kontrolü |
| `GET` | `/game/{game_name}` | Oyun fiyat + indirim bilgisi |
| `GET` | `/docs` | Swagger UI (interaktif API dökümantasyonu) |
| `GET` | `/redoc` | ReDoc dökümantasyonu |

### Örnek İstekler

```powershell
# Sistem durumu
Invoke-RestMethod http://127.0.0.1:8000/status

# Oyun fiyatı (boşluklu isimler için %20 kullan)
Invoke-RestMethod "http://127.0.0.1:8000/game/Cyberpunk%202077"
Invoke-RestMethod "http://127.0.0.1:8000/game/Witcher"
Invoke-RestMethod "http://127.0.0.1:8000/game/GTA"
```

### Örnek Yanıtlar

**GET /status**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development",
  "message": "GamePulse is up and running 🎮"
}
```

**GET /game/Witcher**
```json
{
  "game_name": "The Witcher 3: Wild Hunt",
  "store": "Steam",
  "normal_price": "39.99",
  "sale_price": "9.99",
  "discount_percent": 75.02,
  "deal_url": "https://www.cheapshark.com/redirect?dealID=...",
  "is_fallback": false,
  "source": "CheapShark API"
}
```

**API erişilemediğinde (fallback):**
```json
{
  "game_name": "SomeGame",
  "store": "N/A (Demo)",
  "normal_price": "59.99",
  "sale_price": "29.99",
  "discount_percent": 50.0,
  "deal_url": "https://www.cheapshark.com",
  "is_fallback": true,
  "source": "fallback"
}
```

---

## 🐳 Docker ile Çalıştırma

> **Ön koşul:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) kurulu ve çalışıyor olmalı.

### 1. İmajı build et

```powershell
# gamepulse/ kök dizininde çalıştır
docker build -t gamepulse:latest .
```

`-t gamepulse:latest` → İmaja `gamepulse` adını ve `latest` etiketini verir.  
`.` → Build context olarak geçerli dizini kullan (`.dockerignore` devreye girer).

### 2. Container'ı başlat

```powershell
docker run -d `
  --name gamepulse-api `
  -p 8000:8000 `
  -e APP_ENV=production `
  gamepulse:latest
```

| Bayrak | Açıklama |
|--------|----------|
| `-d` | Detached mode — arka planda çalışır |
| `--name gamepulse-api` | Container'a kolay hatırlanan bir isim ver |
| `-p 8000:8000` | Host:8000 → Container:8000 port yönlendirmesi |
| `-e APP_ENV=production` | Ortam değişkeni enjeksiyonu |

### 3. Çalıştığını doğrula

```powershell
# Container loglarını izle
docker logs -f gamepulse-api

# Sağlık kontrolü
Invoke-RestMethod http://localhost:8000/status

# Swagger UI
Start-Process "http://localhost:8000/docs"
```

### 4. Container yönetimi

```powershell
# Durdur
docker stop gamepulse-api

# Yeniden başlat
docker start gamepulse-api

# Sil (durdurulmuş container)
docker rm gamepulse-api

# İmajı sil
docker rmi gamepulse:latest

# Çalışan tüm container'ları listele
docker ps
```

### 5. İmaj boyutunu kontrol et

```powershell
docker images gamepulse
```

> `python:3.11-slim` tabanlı multi-stage build ile imaj boyutu ~180-200 MB civarında olacaktır  
> (tam `python:3.11` ≈ 1 GB ile kıyaslandığında ciddi tasarruf).

---

## Tasarım Kararları

| Karar | Sebep |
|-------|-------|
| **httpx yerine requests** | Async-native; FastAPI'nin event loop'u ile uyumlu |
| **Fallback pattern** | API bağımlılığı servisi çökertmemeli (resilience) |
| **APIRouter** | Endpoint'leri modüler tutar, ölçeklenebilirlik sağlar |
| **Lifespan context** | Deprecated `@on_event` yerine modern FastAPI yaklaşımı |
| **Global exception handler** | 500 hatalarını yakalar, sunucu ayakta kalır |
| **Pydantic schemas** | Otomatik validasyon + Swagger dökümantasyonu |

---

## Sonraki Adımlar (İleride Eklenebilecekler)

- [ ] Redis cache (aynı oyun için API'yi tekrar çağırma)
- [ ] PostgreSQL ile fiyat geçmişi tutma
- [x] Docker (multi-stage Dockerfile + .dockerignore)
- [ ] GitHub Actions CI/CD pipeline
- [ ] Rate limiting (slowapi)
- [ ] JWT authentication
