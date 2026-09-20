# SISGETRAN Backend

API Django 5.1 + DRF para MySQL 8+. Requiere Python 3.11+ y un servidor MySQL configurado con InnoDB/utf8mb4.

## Instalación

Como administrador de una instancia local MySQL 8, cree una identidad exclusiva de desarrollo (reemplace el valor de ejemplo por una clave local robusta y no la confirme en Git):

```sql
CREATE DATABASE sisgetran_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'sisgetran_dev'@'localhost' IDENTIFIED BY '<clave-local-segura>';
CREATE USER 'sisgetran_dev'@'127.0.0.1' IDENTIFIED BY '<clave-local-segura>';
GRANT ALL PRIVILEGES ON sisgetran_dev.* TO 'sisgetran_dev'@'localhost';
GRANT ALL PRIVILEGES ON sisgetran_dev.* TO 'sisgetran_dev'@'127.0.0.1';
```

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements/development.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo  # opcional; solo datos ficticios
python manage.py runserver
```

Configure `DJANGO_SECRET_KEY`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` y `CORS_ALLOWED_ORIGINS`. No use el usuario `root` de MySQL.

Compruebe el motor real antes de desarrollar:

```powershell
python manage.py migrate
python manage.py check
python manage.py makemigrations --check
python manage.py shell -c "from django.db import connection; print(connection.vendor, connection.mysql_version)"
```

## Verificación

```powershell
pytest
```

Los tests unitarios usan una base SQLite efímera; el checkpoint de entrega debe ejecutar además `migrate`, `check` y la inspección física contra MySQL 8.

OpenAPI: `/api/schema/`; Swagger: `/api/docs/`. El frontend esperado corre en `http://localhost:5173`.
