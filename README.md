# Residence SaaS API

Backend REST API para gestión de condominios residenciales, construido con **FastAPI** (async) + **SQLAlchemy 2.0** + **PostgreSQL**.

## Funcionalidades

### Autenticación (`/api/v1/auth/`)
- Login email + contraseña con verificación PIN por email
- Registro de usuarios
- Recuperación de contraseña
- JWT con refresh tokens
- Endpoint `/me` con propiedades, condominios y roles del usuario

### Visitantes (`/api/v1/visitors/`)
- Registro de entrada/salida por admin/portería
- Pre-registro por residentes (`POST /me`) — crea visitante con `entry_time=NULL`
- Confirmación de entrada por admin (`POST /{id}/confirm-entry`)
- Salida por residente (`POST /me/{id}/exit`)
- Listado de activos (filtrable por `property_id`), pendientes, e historial
- Estado calculado: `pre_registered`, `active`, `exited`

### PQRS (`/api/v1/pqrs/`)
- CRUD de Peticiones, Quejas, Reclamos, Sugerencias
- Cambio de estado y prioridad (admin)
- Resolución de PQRS (admin)
- Comentarios en cada PQR (cualquier usuario autenticado)
- Filtros por estado, tipo y propiedad

### Facturación (`/api/v1/finance/`)
- Facturas, pagos y balances por propiedad
- Filtros por estado de pago

### Amenidades (`/api/v1/amenities/`)
- Listado de áreas comunes
- Reservas (crear, cancelar, mis reservas)
- Gestión de disponibilidad

### Otros módulos
- **Propiedades y residentes** (`/api/v1/properties/`)
- **Usuarios** (`/api/v1/users/`)
- **Catálogos** (`/api/v1/catalogs/`) — Tipos de documento, PQR, estados, prioridades, etc.
- **Notificaciones** (`/api/v1/notifications/`)
- **Dashboard** (`/api/v1/dashboard/`)
- **Noticias** (`/api/v1/news/`)
- **Estacionamientos** (`/api/v1/parking/`)
- **Mascotas** (`/api/v1/pets/`)
- **Chatbot IA** (`/api/v1/chatbot/`) — RAG con Gemini + pgvector

## Requisitos

- Python 3.9+
- PostgreSQL

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

## Seed Data (obligatorio)

La app requiere datos en las tablas de catálogo. Ejecutar antes del primer uso:

```bash
psql -U <usuario> -d <database> -f 001_seed_dev.sql
```

Esto pobla las 14 tablas de catálogo:
- `pqr_types` — Petición, Queja, Reclamo, Sugerencia
- `pqr_statuses` — Abierto, En Proceso, Resuelto, Cerrado
- `priorities` — Baja, Media, Alta, Urgente
- `booking_statuses` — Pendiente, Aprobada, Rechazada, Cancelada, Finalizada
- `payment_statuses` — Pendiente, Pagado, Parcial, Vencido, Anulado
- `payment_methods` — Efectivo, Transferencia, Tarjeta Crédito/Débito, PSE
- `document_types` — CC, CE, Pasaporte, TI, NIT
- `property_types` — Apartamento, Casa, Local, Oficina, Bodega
- `charge_categories`, `relation_types`, `vehicle_types`, `parking_space_types`, `pet_species`, `notification_types`

Los IDs deben coincidir con los enums en `app/core/enums.py`.

## Variables de Entorno

Ver [.env.example](.env.example) para la lista completa.

| Variable | Descripcion |
|---|---|
| `DATABASE_URL` | URL de conexion PostgreSQL (`postgresql+asyncpg://...`) |
| `SECRET_KEY` | Clave secreta para firmar JWT (min. 32 caracteres) |
| `CORS_ORIGINS` | Origenes permitidos (separados por coma) |
| `SMTP_*` | Configuracion SMTP para envio de PINs |
| `GEMINI_API_KEY` | API key de Google Gemini para el chatbot |

## Ejecucion

```bash
# Desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Produccion
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 0.0.0.0:8000
```

## Tests

```bash
python -m pytest tests/ -q
python -m pytest tests/ --tb=short -v  # con detalle
```

## Documentacion API

Con la app corriendo:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Estructura del Proyecto

```
app/
├── core/           # Config, DB, security, exceptions, email, enums, AI
├── models/         # Modelos SQLAlchemy (ORM)
├── schemas/        # Schemas Pydantic (request/response)
└── modules/        # Modulos de negocio
    ├── auth/       # Autenticacion (PIN + JWT)
    ├── users/      # Gestion de usuarios
    ├── properties/ # Propiedades y residentes
    ├── finance/    # Facturacion y pagos
    ├── visitors/   # Control de visitantes (entrada/salida/pre-registro)
    ├── pqrs/       # Peticiones, quejas, reclamos, sugerencias
    ├── amenities/  # Areas comunes y reservas
    ├── catalogs/   # Tablas de catalogo (CRUD generico)
    ├── dashboard/  # Estadisticas del condominio
    ├── notifications/
    ├── chatbot/    # Chatbot IA (RAG con Gemini)
    ├── news/
    ├── parking/
    ├── pets/
    └── condominiums/
001_seed_dev.sql    # Seed data para todas las tablas de catalogo
```
