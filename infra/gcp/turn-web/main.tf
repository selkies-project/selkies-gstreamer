data "google_client_config" "default" {}

provider "docker" {
  registry_auth {
    address  = "gcr.io"
    username = "oauth2accesstoken"
    password = data.google_client_config.default.access_token
  }
}

data "google_secret_manager_secret_version" "selkies-turn-htpasswd" {
  secret = var.htpasswd_secret_name
}

data "google_container_registry_image" "coturn-web-tagged" {
  name = "selkies-gstreamer-coturn-web"
  tag  = var.image_tag
}

data "docker_registry_image" "coturn-web" {
  name = "${data.google_container_registry_image.coturn-web-tagged.image_url}"
}

data "google_container_registry_image" "coturn-web" {
  name   = "selkies-gstreamer-coturn-web"
  digest = length(var.image_digest) == 0 ? data.docker_registry_image.coturn-web.sha256_digest : var.image_digest
}

resource "google_cloud_run_service" "turn-web" {
  provider = google-beta
  project  = var.project_id
  name     = "selkies-turn-web"
  location = var.region

  template {
    spec {
      containers {
        image = data.google_container_registry_image.coturn-web.image_url
        env {
          name  = "CLOUD_RUN"
          value = "true"
        }
        env {
          name  = "TURN_PORT"
          value = "3478"
        }
        env {
          name  = "TURN_SHARED_SECRET"
          value = data.terraform_remote_state.base.outputs.turn_shared_secret
        }
        env {
          name  = "TURN_HTPASSWD_FILE"
          value = "/etc/htpasswd"
        }
        env {
          name  = "HTPASSWD_DATA64"
          value = base64encode(data.google_secret_manager_secret_version.selkies-turn-htpasswd.secret_data)
        }
        env {
          name  = "MIG_DISCO_FILTER"
          value = var.mig_disco_filter
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  autogenerate_revision_name = true

  lifecycle {
    ignore_changes = [
      metadata.0.annotations,
    ]
  }

  depends_on = [data.google_secret_manager_secret_version.selkies-turn-htpasswd]
}

data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location = google_cloud_run_service.turn-web.location
  project  = google_cloud_run_service.turn-web.project
  service  = google_cloud_run_service.turn-web.name

  policy_data = data.google_iam_policy.noauth.policy_data
}