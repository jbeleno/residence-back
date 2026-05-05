# 🏘️ Residence SaaS — Backend

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-3670A0?style=flat-square&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square)](https://www.sqlalchemy.org/)
[![pgvector](https://img.shields.io/badge/pgvector-RAG-4169E1?style=flat-square)](https://github.com/pgvector/pgvector)
[![Gemini](https://img.shields.io/badge/Gemini-AI-8E75B2?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev/)

REST API **asíncrona** para gestión de condominios residenciales. Construida con **FastAPI** + **SQLAlchemy 2.0 async** + **PostgreSQL**, con autenticación por PIN + JWT, módulo de facturación, control de visitantes, PQRS, reservas de amenidades, y un **chatbot RAG** con Gemini y pgvector.

> **Contexto:** Proyecto académico desarrollado para presentación en feria de la **Universidad Surcolombiana (USCO)**. Diseñado como un SaaS funcional, no un demo — incluye 14+ módulos de negocio, autenticación robusta y un chatbot con RAG real.

---

## ✨ Highlights

- ⚡ **Async-first** — FastAPI + SQLAlchemy 2.0 async + asyncpg.
- 🔐 **Autenticación con PIN por email + JWT** (access + refresh tokens).
- 🤖 **Chatbot IA con RAG** — Google Gemini + pgvector para búsqueda semántica sobre el dominio del condominio.
- 🏢 **14+ módulos de negocio**: auth, usuarios, propiedades, finanzas, visitantes, PQRS, amenidades, dashboard, noticias, parking, mascotas, notificaciones, catálogos.
- 📋 **Catálogos versionados** con seed SQL para 14 tablas de referencia.
- 🧪 Suite de tests con `pytest`.
- 📜 Documentación auto-generada con OpenAPI (Swagger UI + ReDoc).

## 🛠️ Tech Stack

| Categoría | Tecnologías |
|-----------|-------------|
| Framework | FastAPI 0.115 (async) |
| ORM | SQLAlchemy 2.0 (async) + asyncpg |
| Base de datos | PostgreSQL + pgvector |
| Validación | Pydantic 2.10 + email-validator |
| Seguridad | python-jose (JWT) · passlib · bcrypt |
| AI / RAG | Google Gemini (chat + embeddings) |
| Cloud SDK | boto3 (AWS) |
| Email | SMTP (Gmail compatible) |
| Servidor | uvicorn (dev) · gunicorn (prod) |
| Testing | pytest |

---

## 🧩 Módulos y endpoints

### 🔑 Autenticación — `/api/v1/auth/`
- Login con email + contraseña, verificación por PIN enviado por email
- Registro de usuarios
- Recuperación de contraseña
- JWT con refresh tokens
- `/me` con propiedades, condominios y roles del usuario

### 👥 Visitantes — `/api/v1/visitors/`
- Registro de entrada/salida por admin/portería
- Pre-registro por residentes (`POST /me`) — crea visitante con `entry_time=NULL`
- Confirmación de entrada por admin (`POST /{id}/confirm-entry`)
- Salida por residente (`POST /me/{id}/exit`)
- Listado de activos, pendientes e historial (filtrable por `property_id`)
- Estados calculados: `pre_registered`, `active`, `exited`

### 📨 PQRS — `/api/v1/pqrs/`
- CRUD de Peticiones, Quejas, Reclamos, Sugerencias
- Cambio de estado y prioridad (admin)
- Resolución (admin)
- Comentarios por usuario autenticado
- Filtros por estado, tipo y propiedad

### 💰 Facturación — `/api/v1/finance/`
- Facturas, pagos y balances por propiedad
- Filtros por estado de pago

### 🏊 Amenidades — `/api/v1/amenities/`
- Listado de áreas comunes
- Reservas (crear, cancelar, mis reservas)
- Gestión de disponibilidad

### 🤖 Chatbot IA — `/api/v1/chatbot/`
- RAG con Google Gemini + pgvector
- Embeddings para búsqueda semántica sobre el dominio del condominio

### 📦 Otros módulos
- **Propiedades y residentes** (`/api/v1/properties/`)
- **Usuarios** (`/api/v1/users/`)
- **Catálogos** (`/api/v1/catalogs/`) — Tipos de documento, PQR, estados, prioridades
- **Notificaciones** (`/api/v1/notifications/`)
- **Dashboard** (`/api/v1/dashboard/`)
- **Noticias** (`/api/v1/news/`)
- **Estacionamientos** (`/api/v1/parking/`)
- **Mascotas** (`/api/v1/pets/`)

---

## 🚀 Instalación local

### Requisitos

- Python 3.9+
- PostgreSQL con extensión `pgvector` instalada

### Pasos

```bash
git clone https://github.com/jbeleno/residence-back.git
cd residence-back

python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

pip install -r requirements.txt

cp .env.example .env
# Editar .env con tus credenciales (DATABASE_URL, SECRET_KEY, SMTP, GEMINI_API_KEY, etc.)
```

### Seed Data (obligatorio)

La app requiere datos iniciales en las tablas de catálogo. Ejecutar antes del primer uso:

```bash
psql -U <usuario> -d <database> -f 001_seed_dev.sql
```

Esto pobla las 14 tablas de catálogo:
`pqr_types`, `pqr_statuses`, `priorities`, `booking_statuses`, `payment_statuses`, `payment_methods`, `document_types`, `property_types`, `charge_categories`, `relation_types`, `vehicle_types`, `parking_space_types`, `pet_species`, `notification_types`.

> Los IDs deben coincidir con los enums en `app/core/enums.py`.

## ⚙️ Variables de entorno

Ver [.env.example](.env.example) para la lista completa.

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | URL de conexión PostgreSQL (`postgresql+asyncpg://...`) |
| `SECRET_KEY` | Clave para firmar JWT (mínimo 32 caracteres) |
| `CORS_ORIGINS` | Orígenes permitidos (separados por coma) |
| `SMTP_*` | Configuración SMTP para envío de PINs |
| `GEMINI_API_KEY` | API key de Google Gemini (chat + embeddings) |

## ▶️ Ejecución

```bash
# Desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Producción
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:8000
```

## 🧪 Tests

```bash
python -m pytest tests/ -q
python -m pytest tests/ --tb=short -v
```

## 📚 Documentación de la API

Con la app corriendo localmente:

- **Swagger UI** (interactivo): http://localhost:8000/docs
- **ReDoc** (lectura limpia): http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

> El despliegue de producción se gestiona internamente para la feria universitaria. Para instancias en vivo, contactar al equipo.

## 📁 Estructura del proyecto

```
app/
├── core/              # Config, DB, security, exceptions, email, enums, AI
├── models/            # Modelos SQLAlchemy (ORM)
├── schemas/           # Schemas Pydantic (request/response)
└── modules/           # Módulos de negocio
    ├── auth/          # Autenticación (PIN + JWT)
    ├── users/
    ├── properties/
    ├── finance/
    ├── visitors/
    ├── pqrs/
    ├── amenities/
    ├── catalogs/
    ├── dashboard/
    ├── notifications/
    ├── chatbot/       # RAG con Gemini + pgvector
    ├── news/
    ├── parking/
    ├── pets/
    └── condominiums/
001_seed_dev.sql       # Seed de tablas de catálogo
ROLES.md               # Documentación de roles y permisos
```

---

## 📄 Licencia

Proyecto académico — Universidad Surcolombiana (USCO).

---

**Desarrollado para la feria de proyectos USCO 2026.**
