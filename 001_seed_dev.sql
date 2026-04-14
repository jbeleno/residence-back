-- ============================================================
-- 001_seed_dev.sql  —  Seed data for all catalog tables
-- IDs MUST stay in sync with app/core/enums.py
-- Run:  psql -U postgres -d residence -f 001_seed_dev.sql
-- ============================================================

BEGIN;

-- ── document_types ──────────────────────────────────────────
INSERT INTO document_types (id, code, name) VALUES
  (1, 'cc',         'Cédula de Ciudadanía'),
  (2, 'ce',         'Cédula de Extranjería'),
  (3, 'pasaporte',  'Pasaporte'),
  (4, 'ti',         'Tarjeta de Identidad'),
  (5, 'nit',        'NIT')
ON CONFLICT (id) DO NOTHING;

-- ── property_types ──────────────────────────────────────────
INSERT INTO property_types (id, code, name) VALUES
  (1, 'apartamento', 'Apartamento'),
  (2, 'casa',        'Casa'),
  (3, 'local',       'Local Comercial'),
  (4, 'oficina',     'Oficina'),
  (5, 'bodega',      'Bodega')
ON CONFLICT (id) DO NOTHING;

-- ── relation_types ──────────────────────────────────────────
INSERT INTO relation_types (id, code, name) VALUES
  (1, 'propietario',  'Propietario'),
  (2, 'arrendatario', 'Arrendatario'),
  (3, 'residente',    'Residente'),
  (4, 'autorizado',   'Autorizado')
ON CONFLICT (id) DO NOTHING;

-- ── booking_statuses ────────────────────────────────────────
-- Sync with BookingStatusEnum
INSERT INTO booking_statuses (id, code, name) VALUES
  (1, 'pendiente',  'Pendiente'),
  (2, 'aprobada',   'Aprobada'),
  (3, 'rechazada',  'Rechazada'),
  (4, 'cancelada',  'Cancelada'),
  (5, 'finalizada', 'Finalizada')
ON CONFLICT (id) DO NOTHING;

-- ── payment_statuses ────────────────────────────────────────
-- Sync with PaymentStatusEnum
INSERT INTO payment_statuses (id, code, name) VALUES
  (1, 'pendiente', 'Pendiente'),
  (2, 'pagado',    'Pagado'),
  (3, 'parcial',   'Parcial'),
  (4, 'vencido',   'Vencido'),
  (5, 'anulado',   'Anulado')
ON CONFLICT (id) DO NOTHING;

-- ── payment_methods ─────────────────────────────────────────
INSERT INTO payment_methods (id, code, name) VALUES
  (1, 'efectivo',         'Efectivo'),
  (2, 'transferencia',    'Transferencia Bancaria'),
  (3, 'tarjeta_credito',  'Tarjeta de Crédito'),
  (4, 'tarjeta_debito',   'Tarjeta de Débito'),
  (5, 'pse',              'PSE')
ON CONFLICT (id) DO NOTHING;

-- ── parking_space_types ─────────────────────────────────────
INSERT INTO parking_space_types (id, code, name) VALUES
  (1, 'cubierto',     'Cubierto'),
  (2, 'descubierto',  'Descubierto'),
  (3, 'visitante',    'Visitante')
ON CONFLICT (id) DO NOTHING;

-- ── vehicle_types ───────────────────────────────────────────
INSERT INTO vehicle_types (id, code, name) VALUES
  (1, 'carro',       'Carro'),
  (2, 'moto',        'Moto'),
  (3, 'bicicleta',   'Bicicleta')
ON CONFLICT (id) DO NOTHING;

-- ── pet_species ─────────────────────────────────────────────
INSERT INTO pet_species (id, code, name) VALUES
  (1, 'perro', 'Perro'),
  (2, 'gato',  'Gato'),
  (3, 'otro',  'Otro')
ON CONFLICT (id) DO NOTHING;

-- ── charge_categories ───────────────────────────────────────
INSERT INTO charge_categories (id, code, name) VALUES
  (1, 'administracion',  'Administración'),
  (2, 'extraordinaria',  'Cuota Extraordinaria'),
  (3, 'multa',           'Multa'),
  (4, 'parqueadero',     'Parqueadero'),
  (5, 'otro',            'Otro')
ON CONFLICT (id) DO NOTHING;

-- ── pqr_types ───────────────────────────────────────────────
INSERT INTO pqr_types (id, code, name) VALUES
  (1, 'peticion',    'Petición'),
  (2, 'queja',       'Queja'),
  (3, 'reclamo',     'Reclamo'),
  (4, 'sugerencia',  'Sugerencia')
ON CONFLICT (id) DO NOTHING;

-- ── pqr_statuses ────────────────────────────────────────────
-- Sync with PqrStatusEnum
INSERT INTO pqr_statuses (id, code, name) VALUES
  (1, 'abierto',    'Abierto'),
  (2, 'en_proceso', 'En Proceso'),
  (3, 'resuelto',   'Resuelto'),
  (4, 'cerrado',    'Cerrado')
ON CONFLICT (id) DO NOTHING;

-- ── priorities ──────────────────────────────────────────────
-- Sync with PriorityEnum
INSERT INTO priorities (id, code, name, level) VALUES
  (1, 'baja',    'Baja',    1),
  (2, 'media',   'Media',   2),
  (3, 'alta',    'Alta',    3),
  (4, 'urgente', 'Urgente', 4)
ON CONFLICT (id) DO NOTHING;

-- ── notification_types ──────────────────────────────────────
INSERT INTO notification_types (id, code, name) VALUES
  (1, 'general',    'General'),
  (2, 'pago',       'Pago'),
  (3, 'reserva',    'Reserva'),
  (4, 'visitante',  'Visitante'),
  (5, 'pqrs',       'PQRS'),
  (6, 'mantenimiento', 'Mantenimiento')
ON CONFLICT (id) DO NOTHING;

-- ── Reset sequences to avoid PK conflicts on future inserts ─
SELECT setval('document_types_id_seq',      (SELECT COALESCE(MAX(id), 0) FROM document_types));
SELECT setval('property_types_id_seq',      (SELECT COALESCE(MAX(id), 0) FROM property_types));
SELECT setval('relation_types_id_seq',      (SELECT COALESCE(MAX(id), 0) FROM relation_types));
SELECT setval('booking_statuses_id_seq',    (SELECT COALESCE(MAX(id), 0) FROM booking_statuses));
SELECT setval('payment_statuses_id_seq',    (SELECT COALESCE(MAX(id), 0) FROM payment_statuses));
SELECT setval('payment_methods_id_seq',     (SELECT COALESCE(MAX(id), 0) FROM payment_methods));
SELECT setval('parking_space_types_id_seq', (SELECT COALESCE(MAX(id), 0) FROM parking_space_types));
SELECT setval('vehicle_types_id_seq',       (SELECT COALESCE(MAX(id), 0) FROM vehicle_types));
SELECT setval('pet_species_id_seq',         (SELECT COALESCE(MAX(id), 0) FROM pet_species));
SELECT setval('charge_categories_id_seq',   (SELECT COALESCE(MAX(id), 0) FROM charge_categories));
SELECT setval('pqr_types_id_seq',           (SELECT COALESCE(MAX(id), 0) FROM pqr_types));
SELECT setval('pqr_statuses_id_seq',        (SELECT COALESCE(MAX(id), 0) FROM pqr_statuses));
SELECT setval('priorities_id_seq',          (SELECT COALESCE(MAX(id), 0) FROM priorities));
SELECT setval('notification_types_id_seq',  (SELECT COALESCE(MAX(id), 0) FROM notification_types));

COMMIT;
