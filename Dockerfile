# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — Dependency installer
# Bağımlılıkları ayrı bir aşamada kurmak Docker layer cache'ini etkin kullanır:
# requirements.txt değişmediği sürece bu katman yeniden build edilmez.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

# Pip'in gereksiz dosya yazmasını engelle (imaj boyutunu küçültür)
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /install

COPY requirements.txt .

RUN pip install --prefix=/install/packages -r requirements.txt


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — Runtime image
# Sadece çalışma zamanı için gereken dosyalar bu aşamaya kopyalanır.
# Builder'daki geçici araçlar (pip, wheel cache, vb.) son imaja girmez.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# ── Ortam değişkenleri ────────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    APP_VERSION=0.1.0

# ── Güvenlik: root olmayan kullanıcı oluştur ──────────────────────────────────
# Container içinde root yetkisiyle çalışmak ciddi bir güvenlik açığıdır.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Builder aşamasında kurulan paketleri kopyala
COPY --from=builder /install/packages /usr/local

# Uygulama kaynak kodunu kopyala
COPY ./app ./app

# Port 8000'i dışarıya aç (docker run -p ile eşleştirilecek)
EXPOSE 8000

# ── Kullanıcıyı değiştir (root'tan appuser'a) ─────────────────────────────────
USER appuser

# ── Üretim başlangıç komutu ───────────────────────────────────────────────────
# --host 0.0.0.0 → container dışından erişim için zorunlu (127.0.0.1 ÇALIŞMAZ)
# --workers 1    → Tek process; ileride Gunicorn + birden fazla worker eklenebilir
# --no-access-log kullanmıyoruz — loglar DevOps için değerli
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]
