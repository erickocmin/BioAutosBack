# D13 — estados de papeleta

## Evidencia del mirror

La auditoría obtuvo 7,259 filas y esta matriz agregada, sin datos personales:

| estado | estadopago | cantidad |
|---:|---:|---:|
| 0 | 1 | 222 |
| 0 | 2 | 444 |
| 0 | 3 | 2 |
| 0 | NULL | 66 |
| 1 | 1 | 3 |
| 1 | 2 | 2 |
| 1 | NULL | 70 |
| 2 | 1 | 5 |
| 2 | 2 | 4 |
| 2 | NULL | 350 |
| 3 | 0 | 4 |
| 3 | 1 | 3,239 |
| 3 | 2 | 2,819 |
| 3 | 3 | 7 |
| 3 | NULL | 22 |

No se asigna significado a ningún número.

## Consulta de producción

```sql
BEGIN READ ONLY;
SELECT estado, estadopago, COUNT(*) AS cantidad
FROM administrativo.papeleta
GROUP BY estado, estadopago
ORDER BY estado, estadopago NULLS LAST;
ROLLBACK;
```

## Preguntas para Operaciones

1. ¿Qué significa cada valor de `estado`?
2. ¿Qué significa cada valor de `estadopago`, incluido `NULL`?
3. ¿Cuáles transiciones están permitidas y cuáles son terminales?
4. ¿Quién cambia cada estado?
5. ¿Un cambio requiere motivo, documento o autorización?
6. ¿`pagoestado` es una tercera dimensión vigente o un campo legado?

## Plantilla de decisión

| Campo | Valor | Significado | Puede pasar a | Responsable | Motivo obligatorio |
|---|---:|---|---|---|---|
| estado | — | Pendiente | — | — | — |
| estadopago | — | Pendiente | — | — | — |

## Resultado D13

**PENDIENTE DE NEGOCIO.** Bloquea `fleet.papeletas`, no el resto de fleet.
