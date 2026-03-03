# Residence SaaS API

Backend REST API para gestión de condominios residenciales, construido con **FastAPI** (async) + **SQLAlchemy 2.0** + **Neon PostgreSQL**.

## Características

- 🏢 Multi-tenant (por condominio)
- 🔐 Autenticación JWT con PIN por email
- 👥 Gestión de usuarios, propiedades, residentes
- 💰 Facturación, pagos y balances
- 🚗 Estacionamientos, mascotas, visitantes
- 📰 Noticias, PQRS, notificaciones
- 🤖 Chatbot IA con RAG (Gemini + pgvector)

## Requisitos

- Python 3.9+
- PostgreSQL (Neon recomendado)

## Instalación

```bash
# Clonar y entrar
git clone <repo-url>
cd residence-back

# Entorno virtual
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

## Variables de Entorno

Ver [.env.example](.env.example) para la lista completa de variables requeridas.

| Variable | Descripción |
|---|---|
| `DATABASE_URL` | URL de conexión PostgreSQL |
| `SECRET_KEY` | Clave secreta para firmar JWT (mín. 32 caracteres) |
| `CORS_ORIGINS` | Orígenes permitidos (separados por coma) |
| `SMTP_*` | Configuración SMTP para envío de PINs |
| `GEMINI_API_KEY` | API key de Google Gemini para el chatbot |

## Ejecución

```bash
# Desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Producción
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:8000
```

## Tests

```bash
# Ejecutar todos los tests
python -m pytest tests/ -q

# Con cobertura
python -m pytest tests/ --tb=short -v
```

## Documentación API

Con la app corriendo, visitar:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Estructura del Proyecto

```
app/
├── core/           # Config, DB, security, exceptions, email, AI
├── models/         # Modelos SQLAlchemy (ORM)
├── schemas/        # Schemas Pydantic (request/response)
└── modules/        # Módulos de negocio (14 módulos)
    ├── auth/       # Autenticación (PIN + JWT)
    ├── users/      # Gestión de usuarios
    ├── properties/ # Propiedades y residentes
    ├── finance/    # Facturación y pagos
    ├── visitors/   # Control de visitantes
    ├── notifications/ # Notificaciones
    ├── chatbot/    # Chatbot IA (RAG)
    └── ...         # amenities, parking, pets, news, pqrs, catalogs, condominiums
tests/
├── conftest.py
├── test_core.py
├── test_auth.py
├── test_users.py
├── test_properties.py
├── test_finance.py
├── test_visitors.py
├── test_notifications.py
├── test_chatbot.py
├── test_condominiums.py
└── test_api_integration.py
```
