# Despliegue de un Cripto Chatbot en Google Kubernetes Engine (GKE)

Se detalla el proceso completo para desplegar una aplicación de chatbot con arquitectura frontend/backend en Google Kubernetes Engine utilizando Artifact Registry para almacenar las imágenes Docker.

## Arquitectura

La aplicación consta de dos componentes:
- **Backend**: API del agente de chatbot
- **Frontend**: Interfaz de usuario web

## Requisitos Previos

- Instancia de Compute Engine (para construcción de imágenes)
- Acceso a Cloud Shell
- API Key de Google (Gemini) para el chatbot

---

## Parte 1: Preparación del Entorno en Compute Engine

### 1.1 Instalación de Docker

Conectarse a la instancia de Compute Engine e instalar Docker (en caso de no estar disponible, en CE debiera estarlo):

```bash
sudo apt install docker
sudo apt-get install docker-compose -y
sudo usermod -aG docker $USER
sudo systemctl start docker
sudo systemctl enable docker
```

### 1.2 Autenticación y Variables de Entorno

```bash
gcloud auth login
```

Configurar las variables de entorno necesarias:

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1
export REPO_NAME=crypto-chatbot-1
echo $PROJECT_ID
```

### 1.3 Clonar el Repositorio

```bash
git clone https://github.com/joserodr72t-create/feb06.git
```

---

## Parte 2: Configuración de Artifact Registry

### 2.1 Habilitar la API

```bash
gcloud services enable artifactregistry.googleapis.com
```

### 2.2 Crear el Repositorio de Imágenes

```bash
gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$REGION \
    --description="Crypto Chatbot images"
```

Verificar la creación:

```bash
gcloud artifacts repositories list --location=$REGION
```

### 2.3 Configurar Autenticación de Docker

```bash
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

---

## Parte 3: Construcción y Publicación de Imágenes

### 3.1 Configurar Variables de Entorno

Antes de construir, editar el archivo `.env` en la carpeta correspondiente:

```bash
cd ~/feb06/gke/frontend
# Editar .env y añadir tu GOOGLE_API_KEY
```

### 3.2 Construir las Imágenes

Construir la imagen del backend:

```bash
cd ~/feb06/gke/backend
docker build -t agent-backend .
```

Construir la imagen del frontend:

```bash
cd ~/feb06/gke/frontend
docker build -t agent-frontend .
```

### 3.3 Etiquetar las Imágenes

```bash
docker tag agent-backend ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/agent-backend:v1
docker tag agent-frontend ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/agent-frontend:v1
```

### 3.4 Subir las Imágenes a Artifact Registry

```bash
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/agent-backend:v1
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/agent-frontend:v1
```

### 3.5 Verificar las Imágenes

```bash
gcloud artifacts docker images list ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}
```

---

## Parte 4: Configuración de GKE desde Cloud Shell

### 4.1 Preparación del Entorno

Abrir Cloud Shell y clonar el repositorio:

```bash
git clone https://github.com/joserodr72t-create/feb06.git
```
Configurar las variables de entorno:

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION=us-central1
export REPO_NAME=crypto-chatbot-1

```

### 4.2 Instalar kubectl (debiera estar por defecto ya)

```bash
sudo apt-get install kubectl
kubectl version --client
```

### 4.3 Instalar el Plugin de Autenticación GKE

```bash
sudo apt-get install google-cloud-cli-gke-gcloud-auth-plugin
gke-gcloud-auth-plugin --version
```

### 4.4 Crear Directorio de Configuración kubectl si no existe

```bash
mkdir -p ~/.kube
```

---

## Parte 5: Creación del Clúster GKE Autopilot

### 5.1 Crear el Clúster

```bash
gcloud container clusters create-auto test-cluster-a \
  --project=$PROJECT_ID \
  --region=$REGION \
  --release-channel=regular
```

> **Nota**: GKE Autopilot gestiona automáticamente la infraestructura del clúster, optimizando costos y seguridad.

### 5.2 Verificar el Estado del Clúster

```bash
gcloud container clusters list
```

---

## Parte 6: Despliegue de la Aplicación

### 6.1 Conectar al Clúster

```bash
gcloud container clusters get-credentials test-cluster-a --region $REGION
```

### 6.2 Navegar a los Manifiestos de Kubernetes

```bash
cd ~/feb06/gke/Kubernetes
```

### 6.3 Crear el Namespace

```bash
kubectl apply -f namespace.yaml
```

### 6.4 Desplegar Backend y Frontend

> **Nota**: Antes debéis modificar los manifiestos para incluir los enlaces a vuestras imagenes.

```bash
kubectl apply -f backend.yaml
kubectl apply -f frontend.yaml
```

### 6.5 Verificar el Despliegue

Comprobar el estado de los pods:

```bash
kubectl get pods -n ucm-master
```

Obtener información de los servicios:

```bash
kubectl get services -n ucm-master
```

---

## Parte 7: Acceso a la Aplicación

Una vez que el servicio tenga asignada una IP externa (columna `EXTERNAL-IP`), acceder al chatbot mediante:

```
http://<EXTERNAL-IP>
```

> **Nota**: La asignación de IP externa puede tardar unos minutos en GKE Autopilot.

---

## Limpieza de Recursos

Para eliminar todos los recursos desplegados:

```bash
kubectl delete -f namespace.yaml
```

Para eliminar el clúster completo:

```bash
gcloud container clusters delete test-cluster-a --region $REGION
```

---

## Resumen de Comandos Rápidos

| Acción | Comando |
|--------|---------|
| Ver pods | `kubectl get pods -n ucm-master` |
| Ver servicios | `kubectl get services -n ucm-master` |
| Ver logs | `kubectl logs <pod-name> -n ucm-master` |
| Describir pod | `kubectl describe pod <pod-name> -n ucm-master` |

---

## Troubleshooting

- **Pods en estado Pending**: Verificar que el clúster Autopilot tenga recursos disponibles
- **ImagePullBackOff**: Comprobar que las imágenes existen en Artifact Registry y que los permisos son correctos
- **Sin IP externa**: Esperar unos minutos o verificar la configuración del servicio tipo LoadBalancer

