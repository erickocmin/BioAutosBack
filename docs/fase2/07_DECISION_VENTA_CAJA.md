# D5 — decisión venta ↔ caja

## Pregunta

> ¿Cómo queremos que el nuevo sistema relacione cada venta con caja y con el arqueo?

## Lo que sabemos

- El análisis exhaustivo del legacy no encontró escritura automática de ventas en `arqueo`, `arqueodetalle` o `arqueoconteo`.
- El arqueo legacy funciona como declaración/conteo manual.
- La ausencia técnica del vínculo no demuestra por sí sola si el desacoplamiento es un control antifraude deliberado o una carencia histórica.

## Lo que no sabemos

- Quién concilia hoy ventas y dinero.
- Si se exige doble control humano.
- Cómo deben impactar pagos mixtos, anulaciones, reprogramaciones, diferencias y cierres ya realizados.

## Opción A — automática

```text
Venta → movimiento de caja inmediato → arqueo
```

Beneficios: saldo casi en tiempo real, menos digitación y vínculo directo venta/dinero.

Consecuencias: exige reversos transaccionales, tratamiento de pagos mixtos y reglas estrictas para cierres; puede eliminar un control manual valioso.

## Opción B — conciliación

```text
Venta → movimiento pendiente → conciliación → caja/arqueo
```

Beneficios: trazabilidad por venta, doble control y detección de diferencias.

Consecuencias: nuevos estados, bandeja operativa, responsables y tiempo límite de conciliación.

## Opción C — manual

```text
Venta     Arqueo manual separado
```

Beneficios: conserva el comportamiento actual y requiere menos cambio operativo inicial.

Consecuencias: baja trazabilidad, mayor error humano y conciliación difícil.

## Recomendación técnica

**Opción B**, porque conserva doble control sin renunciar al rastro venta↔dinero. Es una recomendación no vinculante: no debe implementarse hasta que Caja, Operaciones y Contabilidad definan responsables, estados y excepciones.

## Responsable

Dueño de producto, Caja/Tesorería, Operaciones y Contabilidad.

## Decisión final

**PENDIENTE.** D5 bloquea únicamente `ticketing.treasury-link` y las partes de ventas que necesiten confirmar el efecto económico final; no bloquea por sí sola catálogos fleet.
