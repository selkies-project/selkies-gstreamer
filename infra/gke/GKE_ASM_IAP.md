# GKE Cluster with ASM and IAP

This tutorial walks you through how to deploy a GKE cluster with ASM and IAP enabled.

# Setup environment

1. Set environment variables used throughout this tutorial:

```bash
export CLUSTER=gke-ingress-us-west1
export PROJECT_ID=$(gcloud config get-value project)
export PROJECT_NUM=$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')
export CLUSTER_REGION=us-west1
export CLUSTER_ZONES=us-west1-a,us-west1-b
export WORKLOAD_POOL=${PROJECT_ID}.svc.id.goog
export MESH_ID="proj-${PROJECT_NUM?}"
export NETWORK_NAME="gke-ingress"
export WORKDIR=${PWD}/working
export ASM_LABEL=asm-managed
export ASM_RELEASE_CHANNEL=regular
```

```bash
mkdir -p ${WORKDIR}
```

2. Enable services

```bash
gcloud services enable \
--project=${PROJECT_ID?} \
anthos.googleapis.com \
container.googleapis.com \
compute.googleapis.com \
monitoring.googleapis.com \
logging.googleapis.com \
cloudtrace.googleapis.com \
meshca.googleapis.com \
meshtelemetry.googleapis.com \
meshconfig.googleapis.com \
iamcredentials.googleapis.com \
gkeconnect.googleapis.com \
gkehub.googleapis.com \
multiclusteringress.googleapis.com \
multiclusterservicediscovery.googleapis.com \
stackdriver.googleapis.com \
trafficdirector.googleapis.com \
cloudresourcemanager.googleapis.com
```

# Create GKE Cluster

1. Create network for cluster:

```bash
gcloud compute networks create ${NETWORK_NAME?} \
    --subnet-mode=auto
```

2. Create Autopilot Cluster:

```bash
gcloud container clusters create-auto ${CLUSTER?} \
    --region ${CLUSTER_REGION?} \
    --project=${PROJECT_ID?} \
    --release-channel "regular" \
    --network=${NETWORK_NAME?} \
    --create-subnetwork name=${CLUSTER?} \
    --enable-private-nodes \
    --master-ipv4-cidr "172.16.1.32/28" \
    --no-enable-master-authorized-networks
```

3. Connect to the cluster:

```bash
gcloud container clusters get-credentials ${CLUSTER?} --region ${CLUSTER_REGION?}
```

# Registering cluster to GKE Hub

1. Register cluster to a fleet:

```bash
gcloud container hub memberships register ${CLUSTER?} \
--project=${PROJECT_ID?} \
--gke-cluster=${CLUSTER_REGION?}/${CLUSTER?} \
--enable-workload-identity

gcloud container hub memberships list
```

The output is similar to the following:

```
NAME                  EXTERNAL_ID
gke-ingress-us-west1  7317db05-6de1-44d8-959c-3403f12eda73
```

# Enable the Gateway Controller

1. Install Gateway API CRDs. Before using Gateway resources in GKE you must install the Gateway API Custom Resource Definitions (CRDs) in your cluster.

```bash
kubectl apply -k "github.com/kubernetes-sigs/gateway-api/config/crd?ref=v0.5.0"
```

Once the feature is enabled the Gateway Controller classes will be available in the config cluster

```bash
watch kubectl get gatewayclasses
```

The output should look like:

```
NAME             CONTROLLER
gke-l7-gxlb      networking.gke.io/gateway
gke-l7-rilb      networking.gke.io/gateway
```
> This can take 1-2 minutes.

# Configure DNS and Google managed certificates

1. Create static IP for load balancer:

```bash
gcloud compute addresses create ${CLUSTER?} --global
export GCLB_IP=$(gcloud compute addresses describe ${CLUSTER?} --global --format=json | jq -r '.address')
echo -e "GCLB_IP is ${GCLB_IP}"
```

2. Create free DNS names in the cloud.goog domain using Cloud Endpoints DNS service.

```
cat <<EOF > ${WORKDIR?}/dns-openapi.yaml
swagger: "2.0"
info:
  description: "Cloud Endpoints DNS"
  title: "Cloud Endpoints DNS"
  version: "1.0.0"
paths: {}
host: "${CLUSTER?}.endpoints.${PROJECT_ID?}.cloud.goog"
x-google-endpoints:
- name: "${CLUSTER?}.endpoints.${PROJECT_ID?}.cloud.goog"
  target: "${GCLB_IP?}"
EOF

gcloud endpoints services deploy ${WORKDIR?}/dns-openapi.yaml
```

> This step takes a few minutes to complete.

3. Create managed certificate:

```
cat <<EOF > ${WORKDIR?}/managed-cert.yaml
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: ${CLUSTER?}-managed-cert
  namespace: istio-system
spec:
  domains:
  - "${CLUSTER?}.endpoints.${PROJECT_ID?}.cloud.goog"
EOF

kubectl create namespace istio-system
kubectl apply -f ${WORKDIR?}/managed-cert.yaml
```

4. View the status of your certificates by describing these resources. The spec and status fields show configured data.

```bash
kubectl -n istio-system describe managedcertificate ${CLUSTER?}-managed-cert
```

5. Get the certificate resource name:

```bash
export MANAGED_CERT=$(kubectl -n istio-system get managedcertificate ${CLUSTER?}-managed-cert -ojsonpath='{.status.certificateName}')
echo -e ${MANAGED_CERT?}
```

# Create GKE Ingress with the Gateway Controller

1. Create GKE Gateway:

```
cat <<EOF > ${WORKDIR?}/gke-gateway.yaml
kind: Gateway
apiVersion: gateway.networking.k8s.io/v1beta1
metadata:
  name: external-http
  namespace: istio-system
spec:
  gatewayClassName: gke-l7-gxlb
  listeners:
  - name: ingress-https
    protocol: HTTPS
    port: 443
    hostname: ${CLUSTER?}.endpoints.${PROJECT_ID?}.cloud.goog
    tls:
      mode: Terminate
      options:
        networking.gke.io/pre-shared-certs: ${MANAGED_CERT?}
    allowedRoutes:
      kinds:
      - kind: HTTPRoute
      namespaces:
        from: All
  addresses: 
    - value: "${GCLB_IP?}"
EOF

kubectl apply -f ${WORKDIR?}/gke-gateway.yaml
```

2. Wait until you get a GCLB IP from the Gateway resource. CTRL-C to exit once you have an IP.

```bash
watch kubectl -n istio-system get gateways -o jsonpath='{.items[*].status.addresses[0].value}'
```

Note that it will take several minutes for the GCLB and the SSL Managed Certificate to be created.

Once the GCLB and cert is ready, you can curl the DNS entry and see a message like the one below.

```bash
watch curl -s https://${CLUSTER?}.endpoints.${PROJECT_ID?}.cloud.goog/
```
> This can take several minutes

Expected output, press CTRL-C after you see this.

```
default backend - 404
```

# Install ASM

1. Install ASM using the ControlPlaneRevision resource:

```
cat <<EOF > ${WORKDIR?}/asm.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: istio-system
---
apiVersion: v1
kind: Namespace
metadata:
  name: asm-gateways
  labels:
    istio.io/rev: ${ASM_LABEL?}
---
apiVersion: mesh.cloud.google.com/v1beta1
kind: ControlPlaneRevision
metadata:
  name: asm-managed
  namespace: istio-system
spec:
  type: managed_service
  channel: ${ASM_RELEASE_CHANNEL?}
EOF

kubectl apply -f ${WORKDIR?}/asm.yaml
kubectl wait --for=condition=ProvisioningFinished controlplanerevision asm-managed -n istio-system --timeout 600s
```

2. Enable Envoy access logs.

```
cat <<EOF > ${WORKDIR?}/asm-access-logs.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: istio-asm-managed
  namespace: istio-system
data:
  mesh: |
    accessLogFile: /dev/stdout
    accessLogEncoding: JSON
EOF

kubectl apply -f ${WORKDIR?}/asm-access-logs.yaml
```

3. Deploy ASM ingress gateway. This gateway will be used by apps in the cluster to route traffic with VirtualServices.

```
cat <<EOF > ${WORKDIR?}/asm-gateways-ns.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: asm-gateways
  labels:
    istio.io/rev: ${ASM_LABEL?}
EOF

cat <<EOF > ${WORKDIR?}/asm-ingressgateway-backendconfig.yaml
apiVersion: cloud.google.com/v1
kind: BackendConfig
metadata:
  name: asm-ingress-xlb-config
  namespace: asm-gateways
spec:
  timeoutSec: 86400
  healthCheck:
    type: HTTP
    port: 15021
    requestPath: /healthz/ready
  securityPolicy:
    name: "gclb-fw-policy"
EOF

cat <<EOF > ${WORKDIR?}/asm-ingressgateway-external.yaml
apiVersion: v1
kind: Service
metadata:
  name: asm-ingressgateway-xlb
  namespace: asm-gateways
  annotations:
    cloud.google.com/backend-config: '{"default": "asm-ingress-xlb-config"}'
spec:
  type: ClusterIP
  selector:
    asm: ingressgateway-xlb
  ports:
  - port: 80
    name: http
  - port: 443
    name: https
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: asm-ingressgateway-xlb
  namespace: asm-gateways
spec:
  selector:
    matchLabels:
      asm: ingressgateway-xlb
  template:
    metadata:
      annotations:
        # This is required to tell Anthos Service Mesh to inject the gateway with the
        # required configuration.
        inject.istio.io/templates: gateway
      labels:
        asm: ingressgateway-xlb
        # asm.io/rev: ${ASM_LABEL?} # This is required only if the namespace is not labeled.
    spec:
      containers:
      - name: istio-proxy
        image: auto # The image will automatically update each time the pod starts.
        resources:
          requests:
            cpu: 500m
            memory: 256Mi
EOF

cat <<EOF > ${WORKDIR?}/asm-ingressgateway-external-httproute.yaml
kind: HTTPRoute
apiVersion: gateway.networking.k8s.io/v1beta1
metadata:
  name: asm-ingressgateway-xlb
  namespace: asm-gateways
  labels:
    gateway: external-http
spec:
  parentRefs:
  - kind: Gateway
    name: external-http
    namespace: istio-system
  hostnames:
  - "${CLUSTER?}.endpoints.${PROJECT_ID?}.cloud.goog"
  rules:
  - backendRefs:
    - kind: Service
      name: asm-ingressgateway-xlb
      port: 80
EOF

kubectl apply -f ${WORKDIR?}/asm-gateways-ns.yaml
kubectl apply -f ${WORKDIR?}/asm-ingressgateway-backendconfig.yaml
kubectl apply -f ${WORKDIR?}/asm-ingressgateway-external.yaml
kubectl apply -f ${WORKDIR?}/asm-ingressgateway-external-httproute.yaml
```

> It will take several minutes for the GCLB to update.

4. Deploy default VirtualService to verify that ASM and Gateway are working:

```
cat <<EOF > ${WORKDIR?}/default-service.yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: default
spec:
  selector:
    asm: ingressgateway-xlb
  servers:
    - port:
        number: 80
        name: http
        protocol: HTTP
      # Default gateway handles all hosts
      hosts:
        - "*"
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: default
spec:
  hosts:
    - "*"
  gateways:
    - default
  http:
    - match:
        - uri:
            prefix: /
      # Rewrite / to readiness path
      rewrite:
        uri: /healthz
      # Route to GCLB default http backend in the kube-system namespace.
      route:
        - destination:
            host: default-http-backend.kube-system.svc.cluster.local
            port:
              number: 80
EOF

kubectl apply -f ${WORKDIR?}/default-service.yaml
```

5. Test the endpoint to verify route to ASM ingress gateway and default service:

```bash
curl -s https://${CLUSTER?}.endpoints.${PROJECT_ID?}.cloud.goog/
```

Expected output:

```
alive
```

> It will take several minutes to update the GCLB routes.

# Enable IAP on GCLB

1. Create an oauth credential to be used with IAP:

```bash
curl https://raw.githubusercontent.com/selkies-project/selkies/f6a2e88e3d1bce9f3f1ea28d382b09c546332c46/setup/scripts/create_oauth_client.sh > ${WORKDIR?}/create_oauth_client.sh
chmod +x ${WORKDIR?}/create_oauth_client.sh
```

```bash
eval $(${WORKDIR?}/create_oauth_client.sh ${CLUSTER?})
```

> If you want to authorize users from outside your Google Workspace Domain, you must enable External user types from the [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent?project=) settings page.

> The programmatic OAuth client creation only works on projects with Internal configured OAuth Consent screens. If you previously configured the OAuth client on this project and made the OAuth client external, this script will return an error like this:

```
ERROR: (gcloud.alpha.iap.oauth-clients.create) FAILED_PRECONDITION: Precondition check failed.
```

> To fix this, make the User type in the OAuth Consent screen settings page Internal and try again.

2. Store the OAuth credential in a Kubernetes Secret:

```bash
kubectl create secret generic iap-oauth-secret -n asm-gateways --from-literal=client_id=${CLIENT_ID?} --from-literal=client_secret=${CLIENT_SECRET?}
```

3. Update the BackendConfig with IAP settings

```
cat <<EOF > ${WORKDIR?}/asm-ingressgateway-backendconfig.yaml
apiVersion: cloud.google.com/v1
kind: BackendConfig
metadata:
  name: asm-ingress-xlb-config
  namespace: asm-gateways
spec:
  timeoutSec: 86400
  healthCheck:
    type: HTTP
    port: 15021
    requestPath: /healthz/ready
  securityPolicy:
    name: "gclb-fw-policy"
  iap:
    enabled: true
    oauthclientCredentials:
      clientID: ${CLIENT_ID?}
      clientSecret: ${CLIENT_SECRET?}
      secretName: iap-oauth-secret
EOF

kubectl apply -f ${WORKDIR?}/asm-ingressgateway-backendconfig.yaml
```

> This configuration will take several minutes to update.

> TODO: The Identity-Aware Proxy console page may display an Error for the Backend service saying: "OAuth client for this resource is misconfigured"

4. Grant your account access to the IAP resource:

```bash
export ACCOUNT=$(gcloud config get-value account)

gcloud iap web add-iam-policy-binding \
  --member="user:${ACCOUNT?}" \
  --resource-type=backend-services \
  --role='roles/iap.httpsResourceAccessor'
```

5. You should now be able to access the IAM authenticated resource in your browser at:

```bash
echo -e https://${CLUSTER?}.endpoints.${PROJECT_ID?}.cloud.goog/
```

Your cluster is now ready to host other VirtualServices with IAP authorization.