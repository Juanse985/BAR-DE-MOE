-- Una base de datos por microservicio (patrón database-per-service).
-- Ningún servicio puede leer las tablas del otro: solo se hablan por HTTP.
-- Este script lo ejecuta Postgres una sola vez, al crear el volumen.

CREATE DATABASE auth_db;
CREATE DATABASE parametrizacion_db;

-- Reservadas para los siguientes sprints (M3 a M6).
-- Se dejan creadas para no tener que borrar el volumen más adelante.
CREATE DATABASE inventario_db;
CREATE DATABASE pedidos_db;
CREATE DATABASE facturacion_db;
CREATE DATABASE reportes_db;
