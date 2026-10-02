# SISGETRAN Backend

API Django 5.1 + DRF. En desarrollo usa **SQLite por defecto** (sin instalar nada adicional); MySQL 8+ con InnoDB/utf8mb4 sigue siendo el motor objetivo para producción y es opt-in en desarrollo. Requiere Python 3.11+.

> ¿Primera vez configurando esto en una PC nueva, con el huellero biométrico incluido? Sigue [docs/puesta-en-marcha.md](docs/puesta-en-marcha.md): clona ambos repos, instala dependencias, conecta el huellero por Ethernet y prueba el flujo de registro + reconocimiento paso a paso.

## Instalación rápida (SQLite, para probar ya)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements/development.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py seed_demo   # usuario demo / DemoOnly.2026 + sucursal + huellero demo
python manage.py runserver 0.0.0.0:8000
```

Con esto ya hay un `db.sqlite3` local en la raíz del proyecto y el servidor corriendo. `0.0.0.0:8000` (no `127.0.0.1`) es necesario si vas a conectar un huellero físico desde la red local.

## Instalación contra MySQL 8 real (opcional)

Para validar algo más cercano a producción, cree una instancia MySQL 8 dedicada:

```sql
CREATE DATABASE sisgetran_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'sisgetran_dev'@'127.0.0.1' IDENTIFIED BY '<clave-local-segura>';
GRANT ALL PRIVILEGES ON sisgetran_dev.* TO 'sisgetran_dev'@'127.0.0.1';
```

En `.env`, ponga `USE_SQLITE=false` y complete `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`. No use el usuario `root` de MySQL. Luego repita `migrate` / `seed_demo` / `runserver`.

Compruebe qué motor está activo en cualquier momento:

```powershell
python manage.py shell -c "from django.db import connection; print(connection.vendor)"
```

## Verificación

```powershell
pytest
```

Los tests usan siempre una base SQLite efímera independiente del `USE_SQLITE` del `.env`. Antes de un despliegue real, además de `pytest`, ejecute `migrate`, `check` y `makemigrations --check` contra MySQL 8.

OpenAPI: `/api/schema/`; Swagger: `/api/docs/`. El frontend esperado corre en `http://localhost:5173`.
