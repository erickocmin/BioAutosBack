# Arquitectura backend

Monolito modular Django/DRF por dominio: `core`, `accounts`, `inventory`, `treasury` y `attendance`. La API delega reglas multirregistro a servicios transaccionales; los querysets de listado usan carga selectiva y paginación. `ticketing`, `fleet`, `cargo` y `billing` no existen todavía por decisión explícita de negocio.

Dependencias: `core` es base; `accounts` usa `core`; los demás usan ambas. No hay Redis, Celery, Docker ni microservicios en esta fase.
