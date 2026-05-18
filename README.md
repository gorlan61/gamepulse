# GamePulse 🎮

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?logo=postgresql&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?logo=tailwind-css&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Render](https://img.shields.io/badge/Render-Deployment-black?logo=render&logoColor=white)

[🇬🇧 English](#english) | [🇹🇷 Türkçe](#türkçe)

---

<a name="english"></a>
## 🇬🇧 English

### 🎯 Purpose
**GamePulse** is a modern, real-time game deal tracking and hardware analysis microservice. It fetches the best game deals from multiple stores (Steam, Epic, GOG, etc.) using the CheapShark API and provides an estimated FPS and performance tier analysis based on the user's GPU model. The application features a sleek, dark-themed glassmorphism UI built with Tailwind CSS.

### 🏗️ System Architecture
1. **Frontend (UI)**: Jinja2 Templates + Tailwind CSS (served directly by FastAPI). Features a debounced autocomplete dropdown for game names and real-time fetch rendering.
2. **Backend (API)**: FastAPI (Python). Handles routing, hardware performance calculations (regex-based rule engine), and external API requests via `httpx`.
3. **Caching Layer**: Built-in SQLite Cache (`gamepulse_cache.db`) with a 1-hour TTL to prevent external API rate-limiting and dramatically enhance response times.
4. **Database**: PostgreSQL (Production) / SQLite (Local) via SQLAlchemy. Logs the most recent user searches to display them dynamically on the UI.

### 🛠️ Tech Stack
- **Backend Framework**: FastAPI, Uvicorn, Jinja2
- **Data & ORM**: SQLAlchemy, PostgreSQL (`psycopg2-binary`), SQLite
- **Frontend**: HTML5, Tailwind CSS (CDN), Vanilla JS (Fetch API)
- **DevOps**: Docker (Multi-stage build), Render (PaaS)

### 🚀 Local Setup

1. **Clone the repository & create a virtual environment:**
```powershell
git clone https://github.com/gorlan61/gamepulse.git
cd gamepulse
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. **Install dependencies:**
```powershell
pip install -r requirements.txt
```

3. **Set up environment variables:**
```powershell
Copy-Item .env.example .env
```

4. **Run the server:**
```powershell
python -m uvicorn app.main:app --reload
```
Navigate to `http://127.0.0.1:8000/` to view the UI, or `http://127.0.0.1:8000/docs` for the Swagger API documentation.

### ☁️ Render Deployment
GamePulse is fully configured for PaaS deployment on Render using Docker.
1. Create a new **Web Service** on Render and connect your GitHub repository.
2. Select **Docker** as the runtime environment.
3. Add a **PostgreSQL** database on Render and copy its internal connection string.
4. Set the following Environment Variables in the Web Service:
   - `APP_ENV` = `production`
   - `DATABASE_URL` = `your_render_postgresql_internal_url`
5. Deploy! Render will build the image from the `Dockerfile` and spin up the service.

---

<a name="türkçe"></a>
## 🇹🇷 Türkçe

### 🎯 Proje Amacı
**GamePulse**, gerçek zamanlı oyun fiyat indirimlerini takip eden ve kullanıcıların donanımlarına (GPU) göre tahmini oyun performansı (FPS) sunan modern bir mikro servistir. CheapShark API'sini kullanarak Steam, Epic ve GOG gibi mağazalardaki fırsatları listeler. Tailwind CSS ile tasarlanmış, "glassmorphism" efektlerine sahip koyu temalı çok şık bir web arayüzü barındırır.

### 🏗️ Sistem Mimarisi
1. **Frontend (Önyüz)**: FastAPI tarafından sunulan Jinja2 Şablonları ve Tailwind CSS. Oyun ararken API'yi yormamak için "debounce" mantığıyla çalışan otomatik tamamlama (autocomplete) özelliği içerir.
2. **Backend (Arkayüz)**: FastAPI (Python). İstek yönlendirmelerini, kural tabanlı donanım performansı hesaplamalarını ve `httpx` üzerinden harici API iletişimini yönetir.
3. **Önbellek (Cache) Katmanı**: Harici API limitlerine takılmamak ve performansı uçurmak için 1 saat ömürlü (TTL) yerel SQLite Cache (`gamepulse_cache.db`) altyapısı kullanır.
4. **Veritabanı**: SQLAlchemy destekli PostgreSQL (Canlı ortam) ve SQLite (Yerel ortam). Kullanıcıların yaptığı son aramaları günlüğe kaydeder ve ana sayfada dinamik olarak listeler.

### 🛠️ Teknoloji Yığını
- **Backend Framework**: FastAPI, Uvicorn, Jinja2
- **Veri & ORM**: SQLAlchemy, PostgreSQL (`psycopg2-binary`), SQLite
- **Frontend**: HTML5, Tailwind CSS (CDN), Vanilla JS (Fetch API)
- **DevOps**: Docker (Multi-stage build), Render (PaaS)

### 🚀 Lokalde Kurulum

1. **Projeyi klonlayın ve sanal ortamı aktif edin:**
```powershell
git clone https://github.com/gorlan61/gamepulse.git
cd gamepulse
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. **Bağımlılıkları yükleyin:**
```powershell
pip install -r requirements.txt
```

3. **Ortam değişkenlerini ayarlayın:**
```powershell
Copy-Item .env.example .env
```

4. **Sunucuyu başlatın:**
```powershell
python -m uvicorn app.main:app --reload
```
Arayüzü görmek için tarayıcıda `http://127.0.0.1:8000/` adresine, Swagger API dökümantasyonu için ise `http://127.0.0.1:8000/docs` adresine gidebilirsiniz.

### ☁️ Render Dağıtımı (Deployment)
GamePulse, Docker kullanılarak Render üzerinde çalışacak şekilde (Production-Ready) yapılandırılmıştır.
1. Render'da yeni bir **Web Service** oluşturun ve GitHub reponuzu bağlayın.
2. Çalışma ortamı (Runtime) olarak **Docker**'ı seçin.
3. Render üzerinde yeni bir **PostgreSQL** veritabanı oluşturun ve dâhili bağlantı adresini kopyalayın.
4. Web Service ayarlarına şu Ortam Değişkenlerini (Environment Variables) ekleyin:
   - `APP_ENV` = `production`
   - `DATABASE_URL` = `render_postgresql_dahili_adresi`
5. Deploy butonuna basın! Render, `Dockerfile` üzerinden imajı inşa edip projeyi saniyeler içinde canlıya alacaktır.
