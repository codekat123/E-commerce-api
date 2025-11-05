# E-commerce API

Modular E-commerce REST API built with Django, DRF, JWT auth, Redis caching, and Celery workers. Features include products, categories, cart, orders, coupons & referrals, user profiles, merchant dashboard, recommendations, and an AI helper. OpenAPI docs via Swagger/Redoc.

## Features
- **Auth**: JWT (login/refresh), OTP-based signup, email verification, password reset.
- **Catalog**: Categories, products, ratings.
- **Cart**: Redis-backed per-user cart with throttling.
- **Orders**: Create, status tracking, payment flow.
- **Coupons/Referral**: CRUD, apply, referral link and balance.
- **Profiles**: Customer and merchant profiles.
- **Dashboard**: Merchant analytics, charts, export reports.
- **Recommendations**: Personalized recs, similar and recent products.
- **AI**: Simple AI chat endpoint.
- **Docs**: Swagger UI and Redoc.

## Tech Stack
- Django 5, DRF, SimpleJWT
- PostgreSQL
- Redis (cache + Celery broker/result)
- Celery workers (+ beat for schedules)
- Gunicorn (production), Railway config provided

## Project Structure
```
E-commerce-api/
└─ src/
   ├─ account/            # Auth & OTP
   ├─ ai/                 # AI chat
   ├─ cart/               # Redis-backed cart (ViewSet)
   ├─ coupon/             # Coupons & referrals
   ├─ dashboard/          # Merchant analytics & reports
   ├─ order/              # Orders & payments
   ├─ product/            # Categories, products, ratings
   ├─ recommendations/    # Recs, similar, recent
   ├─ user_profile/       # Customer & merchant profiles
   ├─ src/                # settings.py, urls.py, celery.py
   ├─ manage.py
   ├─ requirements.txt
   ├─ Procfile            # web + worker commands
   └─ railway.toml        # Deploy packages/env
```

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 6+

### Setup
1. Create virtual environment and install deps:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r src/requirements.txt
   ```
2. Create `.env` inside `src/` (template below).
3. Apply migrations and create superuser:
   ```bash
   cd src
   python manage.py migrate
   python manage.py createsuperuser
   ```

### Run Locally
- Django server:
  ```bash
  cd src
  python manage.py runserver
  ```
- Celery worker:
  ```bash
  cd src
  celery -A src worker --loglevel=info
  ```
- Celery beat (schedules):
  ```bash
  cd src
  celery -A src beat --loglevel=info
  ```

## Environment Variables (.env in src/)
Do not commit real secrets. Typical variables used by `src/settings.py`:

- Core
  - `SECRET_KEY`
  - `DEBUG` = True|False
  - (Optional) `ALLOWED_HOSTS`
- Database
  - If `DEBUG=True`:
    - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `HOST`, `PORT`
  - If `DEBUG=False`:
    - `DATABASE_URL` (e.g., postgres://user:pass@host:5432/dbname)
- Email (SMTP)
  - `EMAIL_HOST_USER`
  - `EMAIL_HOST_PASSWORD`
- Redis / Cache
  - `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`
  - `REDIS_USERNAME` (optional)
  - `REDIS_PASSWORD` (optional)
- Celery
  - `CELERY_BROKER_URL` (e.g., redis://...)
  - `CELERY_RESULT_BACKEND` (e.g., redis://...)
- Integrations
  - `GEMINI_API_KEY` (AI)
  - `BREVO_API_KEY` (email/marketing if used)

### Example .env (template)
```
SECRET_KEY=changeme
DEBUG=True

# Dev DB
DB_NAME=ecommerce
DB_USER=postgres
DB_PASSWORD=postgres
HOST=127.0.0.1
PORT=5432

# Or prod:
# DATABASE_URL=postgres://user:pass@host:5432/dbname

# SMTP
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password

# Redis
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
# REDIS_USERNAME=
# REDIS_PASSWORD=

# Celery
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2

# Integrations
# GEMINI_API_KEY=
# BREVO_API_KEY=
```

## API Documentation
- Swagger: `/api/docs/`
- Redoc: `/api/redoc/`
- OpenAPI schema: `/api/schema/`

## URL Map (High Level)
Base prefixes from `src/src/urls.py`:

- **/account/**
  - `login/token/`, `login/token/refresh/`
  - `sign-up/`, `logout/`
  - `activate/`, `resend-otp/`
  - `password/reset/`, `password/reset/verify/`

- **/profile/**
  - `customer/`, `customer/update/`
  - `merchant/`, `merchant/update/`

- **/product/**
  - `categories/`, `categories/<slug:slug>/`
  - `products/`, `products/<slug:slug>/`
  - `products/rate/<slug:slug>/`, `products/rate/update/`

- **/cart/**
  - DRF router for `CartViewSet` (list/add/update/remove — see Swagger)

- **/order/**
  - `create/`
  - `track-order/<order_id>/`
  - `order-payment/<order_id>/`
  - ``, `<uuid:order_id>/` (detail)

- **/coupon/**
  - `products/<slug:slug>/coupons/`
  - `coupons/`, `coupons/<code>/`, `coupons/<code>/update/`, `coupons/<code>/delete/`
  - `apply-coupon/`
  - `get-referral-link/`, `get-referral-balance/`

- **/dashboard/**
  - `products/ordered/`, `products/paid/`
  - `products/create/`, `products/<slug:slug>/update/`
  - `chart/`
  - `report/<str:report_type>/`

- **/recommendations/**
  - `` (user recommendations)
  - `similar-products/<slug:slug>/`
  - `recent-viewed-products/`

- **/ai/**
  - `` (AI chat)

## Caching & Throttling
- Cache: Redis via `django-redis`. Cart cached with ~2-day TTL.
- Throttling (DRF):
  - `anon`: 100/day
  - `user`: 1000/day
  - `login`: 5/minute

## Background Jobs
- Celery app: `src/src/celery.py`
- Example beat: periodic recommendations (`recommendations.task.compute_item_similarity`).
- Run both worker and beat locally.

## Production
- Procfile:
  - `web: gunicorn src.wsgi:application --workers 1 --threads 2 --worker-class gthread --timeout 120 --bind 0.0.0.0:$PORT`
  - `worker: celery -A src worker --loglevel=info`
- Railway:
  - `railway.toml` installs system packages and sets `PYTHONUNBUFFERED`.
  - Configure all env vars in Railway.
- Static/Media:
  - `STATIC_ROOT = src/static/`
  - `MEDIA_ROOT = src/static/media/`


