# D4 — DocumentRoot y exposición del legacy

## Estado

**NO VERIFICABLE desde este entorno.** No hay acceso autorizado a la configuración efectiva ni autorización para sondear el servidor productivo. No se realizaron solicitudes a producción.

## Inspección que debe ejecutar infraestructura

1. Identificar configuración efectiva de Apache/Nginx y cualquier proxy anterior.
2. Registrar, sin secretos: `VirtualHost`, `DocumentRoot`, `Alias`, `ProxyPass` y reglas de acceso aplicables.
3. Confirmar que el contenido público se limita a la carpeta prevista (`web/`) y a archivos estrictamente necesarios.
4. Probar desde una red externa autorizada que estas rutas no son accesibles:

```text
/info.php
/update.php
/ver.php
/.git/
/lib/
/model/
/controller/
```

5. Verificar que una respuesta `403`/`404` no incluya contenido del archivo ni listado de directorio.

Ejemplo de comprobación, sustituyendo únicamente un host aprobado:

```bash
for path in /info.php /update.php /ver.php /.git/ /lib/ /model/ /controller/; do
  curl --fail-with-body --max-time 10 --head "https://HOST_AUTORIZADO${path}"
done
```

## Clasificación

| Resultado | Criterio |
|---|---|
| SEGURO | `DocumentRoot` limitado y todas las rutas sensibles bloqueadas sin contenido |
| RIESGO | Configuración amplia, pero controles compensatorios bloquean las rutas |
| CRÍTICO | Alguna ruta entrega código, configuración, listado, repositorio o ejecuta scripts sensibles |
| NO VERIFICABLE | No se dispone de configuración y prueba autorizada |

## Resultado D4

**NO VERIFICABLE.** Es una acción urgente de infraestructura, pero no bloquea el diseño de subdominios.
