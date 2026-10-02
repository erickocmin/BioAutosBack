# Resultado ejecutivo — Fase 2A

Fecha: 20 de septiembre de 2026.

## D1

**¿Resuelta?** No. Se cerró el inventario técnico de credenciales expuestas sin registrar valores. Todas permanecen `PENDIENTE` hasta recibir evidencia de rotación y revocación.

## D2

**¿Riesgo actual?** No verificable: el mirror no contiene series y no hay acceso autorizado a producción. Se entregó un `SELECT` read-only que clasifica `OK`, `ADVERTENCIA`, `CRÍTICA` y `AGOTADA`.

## D3

**¿Qué falta?** Legal/Operaciones debe identificar el canal oficial actual del Libro de Reclamaciones. No afecta los cuatro dominios operativos analizados.

## D4

**¿Seguro?** No verificable. Se preparó el checklist de configuración y exposición; no se sondeó producción sin autorización.

## D5

**¿Decisión tomada?** No. Se documentaron A automática, B conciliación y C manual. La recomendación técnica preliminar es B, sin autorización para implementarla.

## D6

**¿Qué eran los esquemas?** Está confirmado que no existen en el mirror y que el repositorio no define una fuente alternativa específica. Hay 41/6/16 archivos con referencias a `reglasnegocio`/`logistica`/`caja`; su naturaleza productiva sigue no determinada.

## D7

**¿Producción valida el modelo?** No todavía. Se prepararon consultas agregadas para PK, volumen, nulos, fechas, estados y relaciones fleet, sin PII. Deben ejecutarse con un rol autorizado read-only.

## D8

**¿Cómo funciona SUNAT realmente?** El código guarda e imprime, y puede generar TXT manual; no contiene un circuito automático completo verificable. El receptor externo, el retorno y el CDR siguen pendientes de Facturación/Contabilidad/Infraestructura.

## Hallazgo adicional D17

`regfactura` sí escribe `administrativo.estadocta`, y cheques actualiza esas filas. El módulo llamado “presupuestos” administra `areagrupo`; no se localizó escritor de `administrativo.presupuestos`.

## Semáforo resumido

| Dominio | Subdominio | Estado | Bloqueante principal |
|---|---|---|---|
| fleet | catalogs | 🟡 | D6/D7 |
| fleet | vehicles | 🟡 | D7 |
| fleet | owners | 🟡 | D7 |
| fleet | drivers | 🟡 | D7 |
| fleet | documents | 🟡 | D7 |
| fleet | routes | 🟡 | D7 |
| fleet | lines | 🟡 | D6/D7 |
| fleet | manifests | 🟡 | D2/D7 |
| fleet | papeletas | 🔴 | D13 |
| fleet | debt-validation | 🔴 | D10/D13/D15 |
| ticketing | trips/seats | 🔴 | D7 y fleet no validado |
| ticketing | sales | 🔴 | D5/D7/D16 |
| ticketing | passengers | 🔴 | D16 |
| ticketing | fares/reservations | 🔴 | Reglas y fuentes pendientes |
| ticketing | cancellations/rescheduling | 🔴 | D5/D8 y reglas pendientes |
| ticketing | treasury-link | 🔴 | D5 |
| cargo | customers | 🔴 | D16 |
| cargo | shipments/reception/delivery | 🔴 | D6 |
| cargo | guides/payments/telegiro | 🔴 | D2/D5/D6/D16 y reglas pendientes |
| billing | document-types | 🟡 | D7 |
| billing | series/correlatives | 🔴 | D2 |
| billing | documents | 🔴 | D5/D6/D8/D16 |
| billing | sunat-adapter/cdr | 🔴 | D8 |
| billing | cancellations | 🔴 | D8 y flujo no confirmado |

La matriz detallada está en `13_MATRIZ_SUBDOMINIOS.md`.

## Primer candidato de implementación

**Ninguno está listo hoy.** `fleet-core` es el primer candidato y queda amarillo. Puede pasar a `LISTO PARA IMPLEMENTAR` cuando:

1. D7 confirme en producción entidades, claves y relaciones.
2. D6 identifique o descarte las fuentes que afectan catálogos/líneas.
3. Se delimite el incremento para excluir papeletas y validación de deuda.

No se crearon apps, modelos, migraciones ni módulos React.

## Conclusión

```text
FASE 2A COMPLETADA — NINGÚN SUBDOMINIO LISTO
```

## Seguimiento Fase 2B

La validación productiva D7 aún no fue ejecutada porque no se proporcionó una cuenta read-only autorizada. El script seguro, las instrucciones y la matriz actualizada se documentan en `05_PERFIL_PRODUCCION.md`, `06_FUENTES_D6.md` y `16_FLEET_READINESS.md`. Este seguimiento no cambia retroactivamente el resultado de Fase 2A.
