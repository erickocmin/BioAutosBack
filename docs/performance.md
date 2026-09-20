# Rendimiento

- Paginación server-side (50 por defecto, máximo 200).
- Búsqueda, filtros y ordering con whitelist del ORM.
- `select_related`/`prefetch_related` en listados y `select_for_update` en stock/caja/correlativos.
- Índices derivados de filtros reales; sin índices indiscriminados.
- Kardex append-only y escrituras en lote cuando corresponde.
- El endpoint ADMS solo persiste; el agregado diario se procesa fuera de la petición.
