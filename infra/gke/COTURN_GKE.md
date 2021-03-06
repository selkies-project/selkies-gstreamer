# Coturn on GKE deployment

# Create Shared Static IP

1. Create shared static IP that will be used by the TCP and UDP load balancers:

```bash
gcloud compute addresses create coturn-${CLUSTER_REGION?} \
    --project=${PROJECT_ID?} \
    --region=${CLUSTER_REGION?}
```

2. Get the address of the static IP:

```bash
STATIC_IP=$(gcloud compute addresses describe coturn-${CLUSTER_REGION?} --region ${CLUSTER_REGION?} --format='value(address)')
```

```bash
echo -n "${STATIC_IP?}" > manifests/coturn/TURN_EXTERNAL_IP
```

# Deploy manifests

The K8S manifest kustomization requires a K8S Secret named `turn-shared-secret`.

This secret is generated by the kustomization and read from 2 files:

- `TURN_SHARED_SECRET`: Contains the shared secret used by coturn and apps like coturn-web or directly by the selkies-gstreamer python app.
- `TURN_REALM`: contains the domain that the coturn service is hosted under.

1. Create a TURN_SHARED_SECRET and TURN_REALM file used by the kustomization:

```bash
openssl rand -base64 15 > manifests/coturn/TURN_SHARED_SECRET
```

```bash
echo -n "${CLUSTER?}.endpoints.${PROJECT_ID?}.cloud.goog" > manifests/coturn/TURN_REALM
```

2. Apply the manifests using the kustomization:

```bash
kubectl kustomize manifests/coturn | \
  sed -e 's/${LB_IP}/'${STATIC_IP?}'/g' | \
    kubectl apply -f -
```

3. Verify the deployment by visiting the `/turn/` route:

```bash
echo "https://${CLUSTER?}.endpoints.${PROJECT_ID?}.cloud.goog/turn/"
```

Example output:

```json
{
  "lifetimeDuration": "86400s",
  "iceServers": [
    {
      "urls": [
        "stun:xx.xxx.xxx.xx:3478"
      ]
    },
    {
      "urls": [
        "turn:xx.xxx.xxx.xx:3478?transport=udp"
      ],
      "username": "1642106590-user@example.com",
      "credential": "hHqE7YmBUpvVrIrYOeUQQ/VcP4k="
    }
  ],
  "blockStatus": "NOT_BLOCKED",
  "iceTransportPolicy": "all"
}
```

> NOTE: The `iceServers` list should contain the IP of the LoadBalancer and static IP provisioned earlier.

> Test the stun and turn servers at the Trickle ICE page: https://webrtc.github.io/samples/src/content/peerconnection/trickle-ice/