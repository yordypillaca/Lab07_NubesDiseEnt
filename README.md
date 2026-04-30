# Lab 07 - Balanceo de carga (local + AWS)

Este proyecto implementa **LOGIN + CRUD** y un balanceador:

## Parte A: Entorno local (como la imagen)

Arquitectura:

- Cliente (curl / navegador) → `nginx` (round-robin puerto 80)
- `nginx` → 3 backends (`backend1`, `backend2`, `backend3`)

### Requisitos

- Docker Desktop (Windows)

### Levantar el entorno

```bash
docker compose up --build
```

### Abrir el Frontend

- Abre `http://localhost/`
- Verás la pantalla de **Login**.
- Luego de ingresar, podrás seleccionar **Backend 1/2/3** y ver `Hola mundo 1/2/3` (directo, sin round-robin) y debajo el CRUD.

### Probar balanceo (debe rotar `instance`)

```bash
curl.exe http://localhost/health
curl.exe http://localhost/health
curl.exe http://localhost/health
```

Prueba pedida por el docente (Hola mundo 1/2/3):

```bash
curl.exe http://localhost/backend1/hello
curl.exe http://localhost/backend2/hello
curl.exe http://localhost/backend3/hello
```

### Login (usuario/clave por defecto)

- Usuario: `admin`
- Password: `admin`

En PowerShell, lo más estable es:

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://localhost/api/login `
  -ContentType 'application/json' `
  -Body '{"username":"admin","password":"admin"}'
$token = $login.token
```

El token dura 1 hora.

### CRUD (Items)

Crear:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost/items `
Invoke-RestMethod -Method Post -Uri http://localhost/api/items `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType 'application/json' `
  -Body '{"name":"Laptop","description":"Dell"}'
```

Listar:

```powershell
Invoke-RestMethod -Method Get -Uri http://localhost/items `
Invoke-RestMethod -Method Get -Uri http://localhost/api/items `
  -Headers @{ Authorization = "Bearer $token" }
```

Actualizar:

```powershell
Invoke-RestMethod -Method Put -Uri http://localhost/items/1 `
Invoke-RestMethod -Method Put -Uri http://localhost/api/items/1 `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType 'application/json' `
  -Body '{"name":"Laptop","description":"Actualizada"}'
```

Eliminar:

```powershell
Invoke-RestMethod -Method Delete -Uri http://localhost/items/1 `
Invoke-RestMethod -Method Delete -Uri http://localhost/api/items/1 `
  -Headers @{ Authorization = "Bearer $token" }
```
