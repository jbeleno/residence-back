# Sistema de Roles — Residence

En la plataforma existen **5 roles**. Cada usuario puede tener distintos roles en distintos condominios (un mismo correo puede ser admin del Conjunto A y residente del Conjunto B), pero al iniciar sesión opera **dentro de un solo condominio a la vez**.

---

## 1. Super Admin

**Para qué sirve:** es el rol de la plataforma, no de un condominio. Administra el SaaS completo. Solo debería existir 1 (o muy pocos) en toda la base de datos. Lo crea el equipo técnico al instalar la plataforma — no se autoasigna ni se crea desde la app.

**Qué puede hacer:**

- Crear, listar y eliminar condominios
- Editar datos personales (nombre, teléfono, documento) de **cualquier** usuario de la plataforma
- Transferir residentes entre condominios distintos
- Todo lo que puede hacer un admin (es superset)

**Qué cosas puede tener vinculadas:**

- 0 propiedades (no necesita vivir en ningún conjunto)
- Acceso a todos los condominios sin estar asignado formalmente

**Cuántos:** ideal 1-2 personas en toda la organización.

**Quién lo asigna:** se crea manualmente en BD por el equipo técnico. No hay endpoint público.

---

## 2. Admin

**Para qué sirve:** administra **un condominio específico**. Es el "gerente" del conjunto. Maneja toda la operación interna excepto datos personales de los residentes.

**Qué puede hacer dentro de su condominio:**

- Crear, editar y desactivar **propiedades** (apartamentos/casas)
- Asignar residentes a propiedades, transferirlos entre apartamentos
- Crear cuentas de usuario (residentes, guardas, contadores, otros admins)
- Crear y editar **amenidades** (piscina, cancha, salón social, etc.)
- Aprobar, rechazar o cancelar reservas de amenidades
- Publicar, editar y eliminar **noticias** del condominio
- Gestionar **PQRS** (cambiar estado, asignar responsable)
- Crear **tipos de cobro** y marcar facturas vencidas
- Crear y registrar **facturas y pagos** (igual que el contador)
- Crear espacios de **parqueadero**
- Subir **documentos al chatbot** (reglamentos, manuales)
- Enviar **notificaciones** a usuarios
- Editar **info del condominio** (dirección, teléfono, logo)
- Crear/editar items de **catálogos**
- **Subir logo** del condominio

**Qué cosas puede tener vinculadas:**

- 0 o 1 propiedad (puede vivir en el condo, pero no es obligatorio)
- 1 condominio asignado (puede ser admin de varios condos, pero opera en uno a la vez)
- 1 avatar
- Vehículos y mascotas si vive ahí

**Cuántos:** típicamente 1-2 admins por condominio.

**Quién lo asigna:** un super_admin lo crea, o cuando se está creando un nuevo condominio, el super_admin asigna al primer admin. Después, ese admin puede crear más admins desde `POST /api/v1/users/`.

---

## 3. Contador

**Para qué sirve:** rol especializado **únicamente** en el módulo financiero. Es el tesorero del condominio. No interviene en gestión administrativa.

**Qué puede hacer dentro de su condominio:**

- Ver todas las facturas
- **Crear facturas** (a propiedades específicas)
- **Registrar pagos** (con método de pago, referencia, etc.)
- Ver pagos de facturas
- Consultar balance de propiedades
- Acceso de lectura a finanzas

**Qué NO puede hacer:**

- ❌ Crear tipos de cobro (eso es del admin)
- ❌ Marcar facturas vencidas (`mark-overdue` — del admin)
- ❌ Editar amenidades, propiedades, residentes, news, etc.
- ❌ Subir logo, documentos, ni ninguna imagen
- ❌ Enviar notificaciones

**Qué cosas puede tener vinculadas:**

- 0 o 1 propiedad (puede o no vivir en el condo)
- 1 condominio
- 1 avatar
- Vehículos/mascotas si vive ahí

**Cuántos:** típicamente 1 contador por condominio (puede ser externo, contratista).

**Quién lo asigna:** el admin del condominio crea la cuenta vía `POST /api/v1/users/` con `role_id = 5`.

---

## 4. Guarda

**Para qué sirve:** personal de portería/seguridad. Su trabajo es controlar **entradas y salidas** de visitantes y manejar el parqueadero de visitantes.

**Qué puede hacer dentro de su condominio:**

- Registrar entrada de visitantes (cuando llega alguien sin pre-registro)
- Confirmar entrada de **pre-registros** hechos por residentes
- Registrar salida de visitantes
- Ver lista de visitantes activos y pre-registros pendientes
- Asignar parqueadero a visitantes
- Cobrar parqueo de visitantes (registrar entrada/salida y monto)
- Ver propiedades, residentes y vehículos del condominio (lectura)
- Recibir notificaciones cuando un residente pre-registra un visitante

**Qué NO puede hacer:**

- ❌ Editar info del condominio o propiedades
- ❌ Crear/editar usuarios, amenidades, news, finanzas
- ❌ Aprobar reservas de amenidades
- ❌ Cualquier cosa fuera de portería

**Qué cosas puede tener vinculadas:**

- 0 propiedades (raro que el guarda viva en el condo)
- 1 condominio (uno donde trabaja)
- 1 avatar
- Vehículos personales si registra alguno

**Cuántos:** típicamente 2-3 por condominio (turnos día/noche/relevos).

**Quién lo asigna:** el admin crea la cuenta del guarda vía `POST /api/v1/users/` con `role_id = 3`.

---

## 5. Residente

**Para qué sirve:** rol de los habitantes del condominio (propietarios, arrendatarios, familiares autorizados). Es el "usuario final" — la mayoría de las cuentas serán residentes.

**Qué puede hacer dentro de su condominio:**

- **Ver** propiedades, residentes, amenidades, noticias, info del condominio
- **Pre-registrar visitantes** (mandar al guarda la lista de quien viene a visitarlo)
- Registrar la salida de **sus propios** visitantes
- **Reservar amenidades** (zonas sociales, canchas, salones)
- **Cancelar sus propias reservas**
- Ver **sus facturas** y consultar su saldo pendiente
- **Crear PQRs** (peticiones, quejas, reclamos)
- **Comentar** en sus PQRs
- **Registrar mascotas** de su propiedad y subir su foto
- **Registrar vehículos** de su propiedad
- **Hablar con el chatbot Resi** (consultas en lenguaje natural)
- **Editar su propio perfil** (nombre, teléfono, avatar)
- **Cambiar su contraseña** y **su correo** (con verificación PIN)
- Recibir y leer **notificaciones**

**Qué NO puede hacer:**

- ❌ Ver/editar datos de otros residentes
- ❌ Ninguna acción administrativa, financiera, ni de portería
- ❌ Editar mascotas/vehículos que no son de su apartamento

**Qué cosas puede tener vinculadas:**

| Recurso | Cuántas |
|---|---|
| Propiedades | 1 o más (si vive en varios apartamentos del mismo o distinto condo) |
| Avatar | 1 |
| Mascotas | sin límite (vinculadas a su propiedad) |
| Vehículos | sin límite (vinculados a su propiedad) |
| Visitantes pre-registrados | sin límite |
| Reservas activas | sin límite (sujeto a disponibilidad) |
| Sesiones de chat con Resi | sin límite |
| Dispositivos para push notifications | sin límite (uno por device) |

**Cuántos:** la gran mayoría de cuentas. 100-300+ por condominio según tamaño.

**Quién lo asigna:** el admin crea las cuentas vía `POST /api/v1/users/` con `role_id = 4` (default si no se especifica). **No hay registro público** — solo el admin puede crear residentes.

---

## Resumen visual

| | Super Admin | Admin | Contador | Guarda | Residente |
|---|---|---|---|---|---|
| **Alcance** | Plataforma entera | 1 condo | 1 condo | 1 condo | 1 condo (o más) |
| **Crea usuarios** | ✅ Cualquiera | ✅ Cualquiera del condo | ❌ | ❌ | ❌ |
| **Crea condominios** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Edita propiedades** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Asigna/transfiere residentes** | ✅ + cross-condo | ✅ mismo condo | ❌ | ❌ | ❌ |
| **Edita amenidades** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Aprueba reservas** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Reserva amenidades** | ✅ | ✅ | ✅ (si vive) | ✅ (si vive) | ✅ |
| **Crea facturas y pagos** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Marca vencidas / tipos de cobro** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Maneja portería (visitantes)** | ✅ | ✅ | ❌ | ✅ | ❌ |
| **Pre-registra visitantes** | ✅ | ✅ | ✅ (si vive) | — | ✅ |
| **Publica noticias** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Maneja PQRs (admin side)** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Crea PQRs (como reportante)** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Sube documentos al chatbot** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Habla con el chatbot** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Registra sus mascotas/vehículos** | — | ✅ (si vive) | ✅ (si vive) | ✅ (si vive) | ✅ |
| **Edita su perfil + cambia contraseña/correo** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Edita perfil de otros** | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## Quién asigna a quién — flujo de creación

```
super_admin (creado en BD por el equipo técnico)
   │
   ├── crea condominios
   ├── asigna el primer admin de cada condominio
   │
admin (de un condo)
   │
   ├── crea otros admins del mismo condo
   ├── crea contador del condo
   ├── crea guardas del condo
   ├── crea residentes del condo
   │
residente
   │
   └── solo edita su propio perfil
```

**Importante:** no existe registro público (`/auth/register` fue eliminado). Toda cuenta nace porque un admin (o super_admin) la crea desde `POST /api/v1/users/`. Si el correo ya existe en otro condominio, en vez de fallar, el sistema **auto-vincula** al usuario existente al nuevo condominio con el rol indicado.

---

## Tabla de IDs de roles

Para usar al crear usuarios desde `POST /api/v1/users/` (campo `role_id`):

| ID | Code | Nombre |
|---|---|---|
| 1 | `super_admin` | Super Admin |
| 2 | `admin` | Admin |
| 3 | `guarda` | Guarda |
| 4 | `residente` | Residente (default si no se especifica) |
| 5 | `contador` | Contador |
