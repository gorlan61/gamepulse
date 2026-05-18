# GamePulse 🎮

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python 3.14](https://img.shields.io/badge/Python_3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Render](https://img.shields.io/badge/Render-000000?style=for-the-badge&logo=render&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)

**Canlı Ortam:** [https://gamepulse-1q3y.onrender.com](https://gamepulse-1q3y.onrender.com)

---

## 📝 Proje Özeti & Çözülen Problemler
GamePulse, oyuncuların en uygun oyun fırsatlarını bulmasını ve kendi donanımlarıyla (GPU) bu oyunları hangi grafik ayarlarında kaç FPS ile oynayabileceklerini anında görmelerini sağlayan **gerçek zamanlı ve asenkron bir mikro servistir**.

Sistem, birden çok mağazadaki oyun fırsatlarını CheapShark API'si üzerinden asenkron olarak (`httpx` ile) çeker. Kendi içerisinde barındırdığı **Regex Tabanlı Performans Motoru** ile kullanıcının girdiği ekran kartı modelini analiz ederek (Örn: RTX 4060, RX 580) tahmini FPS ve kalite katmanı (Tier) üretir. Tüm bunları modern, koyu temalı ve *glassmorphism* tasarımlı premium bir arayüzle oyunculara sunar.

---

## 🏗️ Teknik Mimari ve Akış (Architecture)

Sistemin esnek yapısı ve yüksek performanslı veri akışı aşağıdaki şekilde tasarlanmıştır:

```mermaid
graph TD
    A[İstemci / Tarayıcı] -->|1. Arama İsteği| B(SlowAPI Rate Limiter)
    B -.->|Limit Aşıldı| Z[429 Too Many Requests]
    B -->|2. Limit Aşılmadı| C{SQLite Cache Hit/Miss}
    C -->|3. Cache Hit| D[Önbellekten Şimşek Hızında Yanıt]
    C -->|4. Cache Miss| E[Asenkron HTTPX İsteği]
    E -->|5. Dış API Verisi| F[Regex Donanım Analiz Motoru]
    F -->|6. Sonuçları Birleştir| G[(PostgreSQL Search History)]
    G -->|7. Yeni Kaydı Ekle| H[Jinja2 + Tailwind CSS UI Render]
    D --> H
```

**Mimari Kararlar ve Zorlukların Aşılması:**
- **Rate Limiting**: `SlowAPI` katmanı, kötü niyetli botların ve spam isteklerin dış API kotalarını tüketmesini engeller. Limit aşımları UI tarafında kibar bildirimlere dönüştürülür.
- **Bulut Uyumlu Önbellekleme**: İşletim sistemine duyarlı (`os.name == "nt"`) akıllı SQLite Cache katmanı kurgulandı. Render gibi salt-okunur (read-only) container ortamlarında `unable to open database file` hatası almamak için sistem Linux ortamında otomatik olarak geçici ve yazılabilir olan `/tmp/` dizinine geçer.
- **Python 3.14 Uyumsuzluğu**: Python 3.14 (pre-release) ortamındaki `__firstlineno__` çakışması `SQLAlchemy>=2.0.35` sürümüne esnetilerek çözüldü. Eksik wheel dosyaları yüzünden patlayan veritabanı bağlantısı ise modern `psycopg` (v3) saf Python modülü ile değiştirilerek garanti altına alındı.

---

## ⚙️ Proje Özellikleri (Features)
- ⚡ **Asenkron FastAPI:** Uvicorn tabanlı, Pydantic ile güçlü veri doğrulama (Validation).
- 🚀 **Performans Odaklı Cache:** Yerleşik SQLite ile 1 saatlik (TTL) önbellekleme mekanizması.
- 🐘 **Modern Veritabanı:** En yeni `psycopg` (v3) sürücüsü ile yüksek performanslı PostgreSQL entegrasyonu ve son aramaların anlık listelendiği Veritabanı Paneli.
- 🧠 **Akıllı Arama (Debounced Autocomplete):** Arayüzde oyun yazılırken API'yi yormayan, 300ms gecikmeli hızlı oyun öneri motoru.
- 🛡️ **Gelişmiş Güvenlik (SlowAPI):** Dakikada 10 (Analiz) ve 30 (Arama) istek sınırlarıyla donatılmış endpoint koruması.
- 🎨 **Premium UI:** Tailwind CSS ile sıfırdan tasarlanmış z-index sorunlarından arındırılmış tam duyarlı (responsive) UI.

---

## 💻 Yerel Kurulum ve Çalıştırma (Local Setup)

Projeyi yerelde (lokalde) çalıştırmak için aşağıdaki komutları sırasıyla uygulayın:

```bash
# 1. Repoyu Klonlayın
git clone https://github.com/gorlan61/gamepulse.git
cd gamepulse

# 2. Sanal Ortam (Virtual Environment) Oluşturun ve Aktif Edin
python -m venv venv

# Windows PowerShell için:
.\venv\Scripts\Activate.ps1
# Linux / MacOS için:
source venv/bin/activate

# 3. Bağımlılıkları Yükleyin (Uyumlu SQLAlchemy ve Psycopg3 dahil)
pip install -r requirements.txt
```

**Ortam Değişkenleri (.env) Ayarı:**  
Proje kök dizininde `.env` dosyasını yapılandırın:
```env
APP_ENV=development
# SQLite kullanmak isterseniz:
DATABASE_URL=sqlite:///./gamepulse.db
# PostgreSQL kullanmak isterseniz:
# DATABASE_URL=postgresql+psycopg://kullanici:sifre@localhost:5432/gamepulse
```

**Sunucuyu Ayağa Kaldırın:**
```bash
python -m uvicorn app.main:app --reload
```
Tarayıcınızda `http://127.0.0.1:8000` adresine giderek muhteşem arayüze erişebilir, veya API dökümantasyonu için `http://127.0.0.1:8000/docs` adresini ziyaret edebilirsiniz.

---

## 🐳 Docker Kullanımı (Dockerization)

GamePulse, production ortamları için hazır bir multi-stage `Dockerfile` barındırır. İhtiyaç durumunda projeyi konteynerize etmek için:

```bash
# Docker imajını inşa edin
docker build -t gamepulse .

# Konteyneri 8000 portundan dışarıya açarak .env bağlamasıyla çalıştırın
docker run -p 8000:8000 --env-file .env gamepulse
```

---

## 🔮 Gelecek Yol Haritası (Roadmap)
- [x] CheapShark API Entegrasyonu ve Asenkron Mimari
- [x] SQLite Cache Katmanı ve Render Uyumlu `/tmp/` Düzeltmesi
- [x] PostgreSQL Veritabanı ve Son Aramalar Paneli
- [x] SlowAPI ile API Rate Limiting (Hız Sınırlandırma)
- [x] Python 3.14 Uyumluluğu (SQLAlchemy 2.0.49 & Pure Psycopg v3)
- [x] Dinamik Autocomplete (Otomatik Tamamlama) ve Glassmorphism UI
- [ ] JWT Tabanlı Kullanıcı Kimlik Doğrulama (Authentication)
- [ ] GitHub Actions ile Otomatik CI/CD Pipeline
- [ ] Pytest ile Birim ve Entegrasyon Testlerinin Yazılması
