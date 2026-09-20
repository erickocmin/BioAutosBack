# Base de datos

MySQL 8+ con InnoDB y `utf8mb4`. Las migraciones Django crean PK, FK, restricciones únicas, checks e índices documentados en los modelos. SQLite se usa únicamente en tests aislados; nunca como destino operativo.

Índices compuestos principales: sucursal+fecha, usuario+fecha, almacén+producto, producto+almacén+fecha, empleado+fecha y dispositivo+fecha. La unicidad de evento biométrico cubre dispositivo+PIN+timestamp+método.
