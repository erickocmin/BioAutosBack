# Migración PostgreSQL legacy → MySQL 8+

La migración será ETL por dominio hacia el modelo normalizado; no se copiarán las 199 tablas. El origen permanece en solo lectura y no comparte escrituras con Django.

| PostgreSQL | MySQL 8+ | Transformación requerida |
|---|---|---|
| `serial` / secuencia | `BIGINT AUTO_INCREMENT` | Cargar IDs históricos explícitamente, ajustar `AUTO_INCREMENT` al máximo + 1 y validar colisiones. |
| `boolean` | `BOOLEAN` (`TINYINT(1)`) | Normalizar enteros/textos legacy a 0/1; rechazar valores ambiguos. |
| `numeric(p,s)` | `DECIMAL(p,s)` | Preservar precisión; nunca convertir importes a `FLOAT`. Reconciliar sumatorias. |
| `timestamp` | `DATETIME(6)` | Definir que timestamps sin zona provienen de `America/Lima`. |
| `timestamptz` | `DATETIME(6)` UTC | Convertir a UTC al extraer; Django aplica la zona de presentación. |
| `json` / `jsonb` | `JSON` | Validar JSON; reemplazar operadores/índices GIN por consultas e índices funcionales justificados. |
| arrays | tabla hija o `JSON` | Normalizar relaciones consultables; JSON solo para datos opacos no relacionales. |
| `uuid` | `CHAR(36)` o `BINARY(16)` | Este modelo usa `BIGINT`; si aparece UUID externo, convertir explícitamente y conservar mapa. |
| `text` | `LONGTEXT`/`TEXT` | Elegir tamaño según perfilado; no indexar texto completo indiscriminadamente. |
| enum PostgreSQL | `TextChoices` + `VARCHAR`/catálogo | Mapear solo estados confirmados; estados ambiguos quedan crudos y sin lógica. |
| views | vistas MySQL o selector ORM | Reescribir sintaxis y probar plan; evitar trasladar vistas muertas. |
| materialized views | tabla resumen refrescada | MySQL no ofrece equivalente nativo; implementar solo si el perfilado lo exige. |
| funciones PL/pgSQL | servicios Django / SQL MySQL | Eliminar `f_setcorrelativostable`; usar PK nativa. Portar solo lógica vigente y testeada. |
| procedimientos | servicios transaccionales | Reescribir con `transaction.atomic()` y tests de invariantes. |
| triggers | servicios explícitos | Inventariar; no duplicar efectos entre trigger y aplicación. La auditoría confirmó ausencia en flujos centrales. |
| `ILIKE` | `LIKE` con collation CI | Usar collation `utf8mb4_0900_ai_ci` y verificar acentos/case. |
| cast `::tipo` | `CAST(x AS tipo)` | Reescribir cada expresión. |
| `INSERT ... RETURNING` | `AUTO_INCREMENT`/ORM | Django obtiene `lastrowid`; no concatenar `MAX(id)+1`. |
| `DISTINCT ON` | `ROW_NUMBER() OVER (...)` | Encapsular en selector; verificar orden determinista. |
| expresiones PostgreSQL | equivalente MySQL | Revisar `date_trunc`, intervalos, concatenación `||`, regex y funciones JSON individualmente. |
| índices parciales | índice compuesto/columna generada | Medir selectividad; MySQL no soporta el mismo predicado parcial. |
| índices GIN/GiST | FULLTEXT/BTREE/índice funcional | Rediseñar según consulta real, no traducir mecánicamente. |
| FK diferibles | FK InnoDB inmediata | Ordenar cargas padre→hijo o usar staging validado; no desactivar integridad en operación normal. |
| `CHECK` | `CHECK` MySQL 8.0.16+ | Mantener invariantes compatibles y duplicar validación amigable en serializers. |

## Configuración de destino

- MySQL 8+, InnoDB, `utf8mb4`, collation `utf8mb4_0900_ai_ci`.
- Usuario dedicado sin privilegios administrativos.
- Modo estricto `STRICT_TRANS_TABLES`.
- Fechas almacenadas en UTC; negocio presentado en `America/Lima`.

## Flujo ETL y reconciliación

1. Extraer por claves estables y lotes deterministas.
2. Transformar nombres, estados y relaciones según el modelo objetivo.
3. Validar huérfanos, duplicados, rangos y estados antes de cargar.
4. Cargar padres antes que hijos con operaciones idempotentes.
5. Reconciliar conteos, importes, IDs, relaciones, estados, correlativos y fechas.

No se ejecutó una migración productiva en esta fase. Los esqueletos están en `scripts/migration/`.
