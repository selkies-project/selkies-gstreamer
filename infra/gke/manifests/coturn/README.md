# Coturn deployment

Requires K8S Secret named turn-shared-secret which is generated from files:

TURN_SHARED_SECRET: Contains the shared secret used by coturn and apps like coturn-web or directly by the Selkies-GStreamer Python app.

Generate a shared secret with the command below:

```bash
openssl rand -base64 15 > TURN_SHARED_SECRET
```

TURN_REALM: contains the domain that the coturn service is hosted under.