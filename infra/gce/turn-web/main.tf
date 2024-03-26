data "google_client_config" "default" {}

provider "docker" {
  registry_auth {
    address  = "gcr.io"
    username = "oauth2accesstoken"
    password = data.google_client_config.default.access_token
  }
}


data "google_secret_manager_secret_version" "selkies-turn-shared-secret" {
  secret = "selkies-turn-shared-secret"
}

data "google_secret_manager_secret_version" "selkies-turn-htpasswd" {
  secret = var.htpasswd_secret_name
}

data "docker_registry_image" "coturn-web" {
  name = "${var.image_repo}:${var.image_tag}"
}

locals {
  image = "${var.image_repo}@${data.docker_registry_image.coturn-web.sha256_digest}"
}

resource "google_cloud_run_service" "turn-web" {
  provider = google-beta
  project  = var.project_id
  name     = "selkies-turn-web"
  location = var.region

  template {
    spec {
      containers {
        image = local.image
        env {
          name  = "TURN_PORT"
          value = "3478"
        }
        env {
          name  = "TURN_SHARED_SECRET"
          value = data.google_secret_manager_secret_version.selkies-turn-shared-secret.secret_data
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