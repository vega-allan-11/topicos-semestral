# Gestor de Inventario - 3 Pipelines en Azure

API REST (Flask + SQLite) desplegada en Azure Container Instances mediante tres pipelines de GitHub Actions.

## Endpoints

| Metodo | Ruta              | Descripcion            |
|--------|-------------------|------------------------|
| GET    | /health           | Estado del servicio    |
| GET    | /products         | Listar productos       |
| POST   | /products         | Crear producto         |
| GET    | /products/{id}    | Obtener producto       |
| PUT    | /products/{id}    | Actualizar producto    |
| DELETE | /products/{id}    | Eliminar producto      |

## Requisitos previos (una sola vez)

1. Cuenta de Azure con una suscripcion activa.
2. Repositorio en GitHub con estos archivos.
3. Crear un Service Principal y guardarlo como secret `AZURE_CREDENTIALS`:

   ```bash
   az ad sp create-for-rbac --name "sp-pipelines" --role Contributor \
     --scopes /subscriptions/<SUB_ID> --sdk-auth
   ```
   Copiar el JSON completo en: Settings -> Secrets and variables -> Actions -> New secret -> `AZURE_CREDENTIALS`.

## Paso a paso

### 1. Editar el nombre del ACR (debe ser unico global)
Cambiar `acrinventario20260706` en estos tres archivos por un nombre propio:
- `infra/variables.tf`
- `.github/workflows/2-build.yml`
- `.github/workflows/3-deploy.yml`

### 2. Ejecutar Pipeline 1 (Infraestructura)
Actions -> `1-infra` -> Run workflow.
Crea: Resource Group, VNet, Subnet, ACR.

### 3. Crear secrets del ACR
Tras el paso 2, obtener credenciales del ACR:
```bash
az acr credential show --name <TU_ACR> --query "username" -o tsv
az acr credential show --name <TU_ACR> --query "passwords[0].value" -o tsv
```
Guardarlos como secrets `ACR_USER` y `ACR_PASS`.

### 4. Ejecutar Pipeline 2 (Build)
Actions -> `2-build` -> Run workflow.
Corre pruebas, construye la imagen y la publica en ACR con tag `v<numero>` y `latest`.

### 5. Ejecutar Pipeline 3 (Deploy)
Actions -> `3-deploy` -> Run workflow.
Crea el contenedor en ACI dentro de la VNet y muestra estado (`Running`) e IP.

## Nota sobre acceso publico

El ACI se integra con la VNet segun lo pide la asignacion, por lo que su IP es privada.
Para evidencia de "aplicacion accesible" desde internet, en `3-deploy.yml` reemplazar
`--subnet $SUBNET_ID` por:

```
--ip-address Public --dns-name-label inventario-final-2026
```

La app quedara en: `http://inventario-final-2026.eastus.azurecontainer.io`

## Prueba rapida (con IP publica)

```bash
BASE=http://inventario-final-2026.eastus.azurecontainer.io
curl $BASE/health
curl -X POST $BASE/products -H "Content-Type: application/json" \
  -d '{"name":"Teclado","quantity":10,"price":25.5}'
curl $BASE/products
```
