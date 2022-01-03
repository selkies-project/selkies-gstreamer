# Coturn on GKE deployment

# Create firewall rule

1. Create a firewall rule to allow traffic to the coturn nodes.

```bash
gcloud compute firewall-rules create allow-turn \
    --project ${PROJECT_ID?} \
    --network ${NETWORK_NAME?} \
    --allow tcp:3478,tcp:25000-25100,udp:3478,udp:25000-25100
```