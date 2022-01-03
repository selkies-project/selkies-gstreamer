# Coturn deployment for VM based TURN servers

Requires the following files to exist before applying the kustomization:

- MIG_DISCO_FILTER: string in the form of `selkies-turn-${REGION}.*`
- MIG_DISCO_PROJECT_ID: string of the project ID where the TURN instances are deployed. This is typically the same project as the cluster.
- TURN_REALM: string of the URL where the turn-web will be hosted from, for default selkies cluster: `broker.endpoints.PROJECT_ID.cloud.goog`
- TURN_SHARED_SECRET: string value of the secret used when creating the coturn-vms, this is stored in a Secret Manager Secret called `selkies-turn-shared-secret`

## Workload Identity

The coturn-web service discovers the external VM IPs using the Compute Engine APIs and requires service account permissions to do so.

The cluster should be running with Workload Identity enabled