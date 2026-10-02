# Puesta en marcha local (backend + frontend + huellero)

Guía única para dejar SISGETRAN operativo en una PC nueva: clonar ambos repos, instalar dependencias, elegir base de datos, conectar el huellero físico y probar el flujo completo (registrar empleado → enrolar huella → ver la marcación en vivo).

Requisitos de la máquina: Python 3.11+, Node 20+ (probado con Node 24), Git. En desarrollo el sistema usa **SQLite por defecto** (no hace falta instalar nada más para probar); MySQL 8 sigue siendo el motor objetivo de producción y es opcional en desarrollo (paso 2.3).

## 1. Clonar o actualizar los repositorios

Primera vez:

```powershell
cd C:\Users\jimmy\OneDrive\Escritorio\old
git clone https://github.com/erickocmin/BioAutosBack.git sisgetran-backend
git clone https://github.com/erickocmin/BioAutosFront.git sisgetran-frontend
```

Si ya los tienes clonados y solo quieres traer lo último:

```powershell
cd C:\Users\jimmy\OneDrive\Escritorio\old\sisgetran-backend
git pull origin phase2/decisions

cd C:\Users\jimmy\OneDrive\Escritorio\old\sisgetran-frontend
git pull origin master
```

## 2. Backend (Django)

### 2.1 Requirements

Las dependencias están separadas por entorno en `requirements/`:

`requirements/base.txt` (siempre necesario):

```
Django==5.1.15
djangorestframework==3.15.2
djangorestframework-simplejwt==5.5.1
django-filter==24.3
django-cors-headers==4.9.0
drf-spectacular==0.28.0
django-environ==0.11.2
PyMySQL==1.2.3
```

`requirements/development.txt` agrega sobre base.txt (para desarrollo y tests): `pytest`, `pytest-django`, `factory-boy`, `freezegun`.

`requirements/production.txt` agrega sobre base.txt: `gunicorn`.

Para desarrollo local instala siempre development.txt (incluye base.txt automáticamente vía `-r base.txt`):

```powershell
cd sisgetran-backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements\development.txt
```

### 2.2 Variables de entorno

```powershell
Copy-Item .env.example .env
```

Edita `.env` y define al menos `DJANGO_SECRET_KEY` (cualquier cadena larga aleatoria en desarrollo) y `CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173`.

### 2.3 Base de datos: SQLite por defecto, MySQL opcional

No tienes que hacer nada para usar SQLite: es el valor por defecto en desarrollo (`USE_SQLITE` por defecto es `true` en `config/settings/development.py`). Django crea un archivo `db.sqlite3` en la raíz del backend la primera vez que corres `migrate`. Esto es suficiente para instalar, registrar usuarios y probar el huellero (sección 5).

**MySQL (opcional, para validar algo más cercano a producción):**

```sql
CREATE DATABASE sisgetran_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
CREATE USER 'sisgetran_dev'@'127.0.0.1' IDENTIFIED BY '<clave-local-segura>';
GRANT ALL PRIVILEGES ON sisgetran_dev.* TO 'sisgetran_dev'@'127.0.0.1';
```

En `.env`, agrega `USE_SQLITE=false` y completa `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST=127.0.0.1`, `DB_PORT=3306`. Si cambias entre SQLite y MySQL, los datos no se comparten entre ambos motores: cada uno tiene su propio set de usuarios/empleados/eventos.

### 2.4 Migrar y levantar el servidor

```powershell
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 0.0.0.0:8000
```

`seed_demo` crea datos ficticios para probar de inmediato: usuario `demo` / contraseña `DemoOnly.2026`, una sucursal demo y un huellero demo. `0.0.0.0:8000` (no `127.0.0.1`) es obligatorio para que el huellero físico, que está en otra IP de la red, pueda llegar al servidor.

## 3. Frontend (React + Vite)

No usa `requirements.txt`: Node resuelve todo desde `package.json` con `npm install`. Dependencias clave: React 19, React Router 7, TanStack Query 5, Axios, Zod, React Hook Form; como herramientas de desarrollo, Vite 8, TypeScript 6, Playwright y Vitest.

```powershell
cd ..\sisgetran-frontend
npm install
Copy-Item .env.example .env
npm run dev
```

El `.env.example` ya trae `VITE_API_URL=http://localhost:8000/api/v1`, que apunta al backend del paso 2. Abre `http://localhost:5173` e inicia sesión (usuario `demo`, contraseña `DemoOnly.2026` si usaste `seed_demo`).

## 4. Conectar y configurar el huellero físico

Aplica a equipos ZKTeco con protocolo ADMS/iClock (por ejemplo, serie `CMYD231760447`), que se conectan solo por Ethernet.

### 4.1 Elegir cómo conectarlo: laptop directa o red compartida

- **Laptop directa (cable del huellero al puerto Ethernet de la laptop):** aísla el huellero de cualquier otra red, pero exige que la laptop tenga una IP fija en la misma subred que el huellero (revisa la IP que trae configurada el equipo de fábrica, normalmente en su pantalla de red). Útil para una prueba rápida de escritorio.
- **Misma red (router o switch Ethernet):** conecta el huellero y la laptop al mismo router/switch. Es la opción recomendada para dejar el puesto operativo, porque la laptop obtiene su IP por DHCP normalmente y el huellero puede quedarse fijo apuntando a esa IP.

Pasos para la opción de red compartida:

1. Conecta el huellero al router/switch con el cable Ethernet que trae.
2. Conecta la laptop (donde corre el backend) al mismo router/switch.
3. Levanta el backend (`runserver 0.0.0.0:8000`, paso 2.4) y abre en el frontend la pantalla **Reconocimiento** (`/attendance/biometric`): el panel "Apunta el equipo a esta PC" detecta y muestra las IPs LAN de la laptop (por ejemplo `192.168.1.20`). Usa esa IP, nunca `localhost` (en el huellero, `localhost` apuntaría al propio equipo, no a la laptop).
4. En el huellero: **Menú → COMM (Comunicación) → Cloud Server / ADMS**.
   - `Server Address`: la IP LAN de la laptop detectada en el paso 3.
   - `Server Port`: `8000`.
   - `Enable Domain Name`: desactivado.
   - `HTTPS`: desactivado (red local sin certificado).
5. Guarda. Algunos modelos piden reiniciar el servicio de red o el equipo para aplicar el cambio.

### 4.2 Abrir el firewall de Windows (una sola vez, como administrador)

Sin esto, Windows bloquea las conexiones entrantes del huellero aunque el backend esté corriendo:

```powershell
New-NetFirewallRule -DisplayName "SISGETRAN Backend 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Profile Private -Action Allow
```

### 4.3 Autorizar el huellero dentro de SISGETRAN

En la pantalla **Reconocimiento** (`/attendance/biometric`), sección "Autorizar huellero":

1. Número de serie: el que trae el equipo (ej. `CMYD231760447`).
2. Nombre, sucursal y ubicación (libres).
3. IP del huellero (la que configuraste o la que tiene asignada en su propia red) y puerto `4370` (puerto propio del equipo; SISGETRAN lo usa solo para el botón "Probar red", no para recibir datos).
4. Guardar.

En cuanto el huellero haga su primer *handshake* contra `/iclock/cdata`, el indicador pasa de "Esperando conexión" a "Huellero comunicado" (orbe verde) en esa misma pantalla.

## 5. Probar el flujo completo: registrar y luego reconocer

1. Ve a **Registrar empleado** (`/attendance/registro`) y completa: usuario, correo, clave temporal, nombres, apellidos, documento, código de empleado, cargo, un PIN biométrico (el que quieras, ej. `1001`), sucursal y, si ya autorizaste el huellero, selecciónalo — eso encola en el equipo el alta `USERINFO` con ese PIN y nombre.
2. Pulsa "Registrar usuario". SISGETRAN confirma el PIN asignado y, si encolaste el alta, te avisa que quedó pendiente de enviarse al huellero.
3. En el huellero físico, enrola la huella (o el rostro, si el modelo lo soporta) para ese mismo PIN: **Menú → User Manage → selecciona el PIN → Enroll Fingerprint** (o Enroll Face). Si no encolaste el alta en el paso 1, da de alta el usuario manualmente en el equipo con ese PIN antes de enrolar.
4. Pide a la persona que marque en el equipo.
5. Vuelve a **Reconocimiento** (`/attendance/biometric`): la marcación aparece en "Entradas y salidas recientes" en un máximo de 4 segundos, con el nombre, el PIN, si fue entrada o salida y el método usado.
6. Si alguien marca con un PIN que todavía no registraste en SISGETRAN, esa misma pantalla muestra el aviso "N marcación(es) con PIN sin asociar" con un enlace a "Completar registro del empleado". En cuanto lo registras con ese PIN desde el paso 1, la marcación pendiente se vincula sola — no hace falta reenviarla ni que la persona vuelva a marcar.

## 6. Problemas comunes

- **El huellero nunca pasa a "Huellero comunicado":** revisa que el backend esté con `0.0.0.0:8000` (no `127.0.0.1`), que el firewall (4.2) esté aplicado, y que el huellero tenga configurada la IP LAN real de la laptop (no `localhost`) en su menú ADMS.
- **Error de conexión a MySQL al migrar:** solo pasa si pusiste `USE_SQLITE=false` sin tener MySQL instalado/corriendo. Quita esa línea del `.env` (o pon `USE_SQLITE=true`) para volver al valor por defecto, que no necesita MySQL.
- **Una marcación se queda con "PIN sin asociar" después de registrar al empleado:** confirma que el PIN biométrico usado al registrar es exactamente el mismo que el PIN con el que marcó el huellero (son cadenas, por lo que `01001` y `1001` no coinciden).
