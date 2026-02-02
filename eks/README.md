# Despliegue de Aplicaciones una aplicación de e-commerce en Amazon EKS


---

## Parte 1: Preparación del Entorno

### 1.1 Verificar Identidad en AWS

Antes de comenzar, confirma que estás autenticado correctamente en AWS:

```bash
aws sts get-caller-identity
```

Este comando muestra Account ID, ARN del usuario/rol y el User ID, confirmando que tienes acceso suficiente.

### 1.2 Verificar kubectl

kubectl viene preinstalado en AWS CloudShell. Puedes verificar su disponibilidad con:

```bash
kubectl version --client
```

---

## Parte 2: Instalación de Herramientas

### 2.1 Instalación de eksctl

eksctl es la herramienta oficial de línea de comandos para crear y gestionar clústeres en Amazon EKS.

```bash
# Descargar y extraer eksctl
curl --silent --location \
  "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" \
  | tar xz -C /tmp

# Mover al directorio de binarios del sistema
sudo mv /tmp/eksctl /usr/local/bin/eksctl

# Verificar la instalación
eksctl version
```

### 2.2 Instalación de Helm

Helm es el gestor de paquetes para Kubernetes, permitiendo instalar y gestionar aplicaciones complejas mediante "charts".

```bash
# Descargar el tarball de Helm v3.15.0
curl -LO https://get.helm.sh/helm-v3.15.0-linux-amd64.tar.gz

# Extraer el contenido
tar -zxvf helm-v3.15.0-linux-amd64.tar.gz

# Mover el binario al PATH del sistema
sudo mv linux-amd64/helm /usr/local/bin/helm

# Verificar la instalación
helm version
```

---

## Parte 3: Creación del Clúster EKS

### 3.1 Clonar el Repositorio

```bash
git clone https://github.com/joserodr72t-create/feb06.git
cd feb06/eks
```

### 3.2 Configurar Variables de Entorno

```bash
export REGION=us-east-1
export CLUSTER_NAME=cluster-ucm
```

### 3.3 Crear el Clúster

El clúster se crea usando un archivo de configuración YAML que define los nodos como instancias t3.medium:

```bash
eksctl create cluster -f cluster.yaml
```

> **Nota:** Este proceso puede tomar entre 15-20 minutos. eksctl creará automáticamente el clúster, los nodos worker, los roles IAM necesarios y la configuración de red (VPC, subnets, security groups).

### 3.4 Configurar kubectl

Una vez creado el clúster, configura kubectl para conectarse:

```bash
aws eks update-kubeconfig --region "$REGION" --name "$CLUSTER_NAME"
```

Este comando actualiza el archivo `~/.kube/config` con las credenciales y el endpoint del clúster.

---

## Parte 4: Despliegue de la Aplicación

### 4.1 Explorar la Estructura de la Aplicación

Examina los manifiestos de Kubernetes del componente catalog:

```bash
ls ./base-application/catalog
```

### 4.2 Desplegar el Componente Catalog

```bash
kubectl apply -k ./base-application/catalog
```

### 4.3 Verificar el Despliegue

Verificar que el namespace fue creado:

```bash
kubectl get namespaces -l app.kubernetes.io/created-by=eks-workshop
```

Verificar el estado de los nodos:

```bash
kubectl get nodes
```

Verificar los pods en el namespace catalog:

```bash
kubectl get pod -n catalog
```

Obtener detalles de un pod específico (reemplazar `<pod-name>` con el nombre real del pod):

```bash
kubectl describe pod <pod-name> -n catalog
```

Verificar los servicios creados:

```bash
kubectl get svc -n catalog
```

### 4.4 Desplegar el Resto de Componentes

```bash
kubectl apply -k ./base-application
```

---

## Anexo: El Flag -k en kubectl (Kustomize)

### ¿Qué es Kustomize?

Kustomize es una herramienta integrada en kubectl que permite personalizar configuraciones de Kubernetes sin modificar los archivos YAML originales.

### ¿Qué hace el flag -k?

Cuando se usa `kubectl apply -k <directorio>`, kubectl:

1. Busca un archivo `kustomization.yaml` en el directorio especificado
2. Procesa todas las transformaciones definidas (patches, overlays, variables)
3. Combina y aplica los recursos resultantes al clúster

### Diferencia entre -f y -k

| Flag | Comportamiento |
|------|----------------|
| `-f` | Aplica directamente el archivo o directorio especificado |
| `-k` | Procesa primero con Kustomize y luego aplica el resultado |




## Parte 5: Configuración de IAM para el Load Balancer Controller

### 5.1 Asociar Proveedor OIDC

El proveedor OIDC permite que los pods de Kubernetes asuman roles de IAM (IRSA - IAM Roles for Service Accounts):

```bash
# Verificar si OIDC está asociado
aws eks describe-cluster --name cluster-ucm \
  --query "cluster.identity.oidc.issuer" --output text

# Asociar proveedor OIDC
eksctl utils associate-iam-oidc-provider \
  --cluster cluster-ucm \
  --approve
```

> **✔ Verificación:** Debería mostrar la URL del emisor OIDC o confirmar que ya está asociado.

### 5.2 Descargar Política IAM

```bash
curl -o iam_policy.json \
  https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json
```

### 5.3 Crear Política IAM

```bash
# Verificar si la política existe
aws iam get-policy \
  --policy-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/AWSLoadBalancerControllerIAMPolicy

# Crear si no existe
aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam_policy.json
```

> **Nota:** Si recibes el error "EntityAlreadyExists", la política ya existe y puedes continuar.

### 5.4 Crear Cuenta de Servicio IAM con IRSA

```bash
# Obtener tu ID de cuenta
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "ID de Cuenta: $AWS_ACCOUNT_ID"

# Crear la cuenta de servicio IAM
eksctl create iamserviceaccount \
  --cluster cluster-ucm \
  --namespace kube-system \
  --name aws-load-balancer-controller-sa \
  --attach-policy-arn arn:aws:iam::${AWS_ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy \
  --override-existing-serviceaccounts \
  --approve
```

### 5.5 Verificar Cuenta de Servicio

```bash
# Verificar que la cuenta de servicio existe con la anotación correcta
kubectl get sa aws-load-balancer-controller-sa -n kube-system -o yaml | grep -A3 annotations
```

> **✔ Verificación:** Debe mostrar un `eks.amazonaws.com/role-arn` con un ARN válido:
> ```yaml
> annotations:
>   eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/eksctl-cluster-ucm-addon-iamserviceaccount-...
> ```

> **⚠️ Si role-arn está vacío, vuelve a ejecutar el paso 5.4.**

```bash
# Verificación adicional con eksctl
eksctl get iamserviceaccount --cluster cluster-ucm
```

---

## Parte 6: Instalar AWS Load Balancer Controller

### 6.1 Agregar Repositorio Helm

```bash
helm repo add eks-charts https://aws.github.io/eks-charts
helm repo update
```

### 6.2 Instalar el Controlador

```bash
helm install aws-load-balancer-controller eks-charts/aws-load-balancer-controller \
  --namespace kube-system \
  --set clusterName=cluster-ucm \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller-sa \
  --wait
```

**Parámetros clave:**

| Parámetro | Valor | Propósito |
|-----------|-------|-----------|
| `serviceAccount.create` | `false` | Usar SA existente (creado por eksctl) |
| `serviceAccount.name` | `aws-load-balancer-controller-sa` | Referenciar nuestra SA habilitada con IRSA |

### 6.3 Verificar Despliegue del Controlador

```bash
kubectl get deployment aws-load-balancer-controller -n kube-system
```

> **✔ Verificación:** Debería mostrar `READY 2/2` (o 1/1 dependiendo de la versión).

### 6.4 Verificar Service Account del Controlador

```bash
kubectl get deployment aws-load-balancer-controller -n kube-system \
  -o jsonpath='{.spec.template.spec.serviceAccountName}'
```

> **✔ Verificación:** Debería mostrar `aws-load-balancer-controller-sa`.

### 6.5 Revisar Logs del Controlador

```bash
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller --tail=20
```

> **✔ Verificación:** Sin errores `403` o `AccessDenied`. Debería mostrar inicio exitoso.

---

## Parte 7: Exponer la Aplicación con NLB

### 7.1 Examinar nlb.yaml

```bash
cat nlb.yaml
```

### 7.2 Aplicar el Servicio

```bash
kubectl apply -f nlb.yaml
```

### 7.3 Observar la Asignación de IP Externa

```bash
kubectl get service ui-nlb -n ui -w
```

> **✔ Verificación:** Después de 1-3 minutos, `EXTERNAL-IP` cambiará de `<pending>` a un nombre DNS:
> ```
> k8s-ui-uinlb-xxxxxxxxxx-yyyyyyyyyyyy.elb.us-east-1.amazonaws.com
> ```

### 7.4 Verificar en AWS (opcional)

```bash
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[?contains(LoadBalancerName, `ui-nlb`)].{Name:LoadBalancerName,DNS:DNSName,State:State.Code}'
```

---

## Parte 8: Probar el Servicio

### 8.1 Obtener el DNS del NLB

```bash
export NLB_DNS=$(kubectl get service ui-nlb -n ui -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "DNS del NLB: $NLB_DNS"
```

### 8.2 Probar Conectividad

```bash
# Esperar la propagación DNS (puede tomar 1-2 minutos)
curl -v http://$NLB_DNS
```

> **✔ Verificación:** Se recibe una respuesta HTTP de la aplicación UI.




---

## Limpieza del Entorno

Para eliminar todos los recursos creados:

```bash
# Eliminar el NLB primero (importante para evitar recursos huérfanos)
kubectl delete -f nlb.yaml

# Eliminar la aplicación
kubectl delete -k ./base-application

# Desinstalar el Load Balancer Controller
helm uninstall aws-load-balancer-controller -n kube-system

# Eliminar el clúster (esto puede tomar varios minutos)
eksctl delete cluster --name "$CLUSTER_NAME" --region "$REGION"
```




