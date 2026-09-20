# Migración de datos

No se transfirieron datos productivos. El ETL futuro ejecutará extract→transform→validate→load por dominio. Nunca importará contraseñas planas ni datos biométricos innecesarios. La reconciliación cubre conteos, sumas, IDs, relaciones, estados, correlativos y fechas. Véase `../MIGRACION_POSTGRESQL_MYSQL.md`.
