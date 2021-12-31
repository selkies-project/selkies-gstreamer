// Key used to sign HMAC credentials, must be used by all instances.
resource "random_password" "turn-shared-secret" {
  length  = 16
  special = false
}

resource "random_password" "web-htpasswd-secret" {
  length = 11
  special = false
}

resource "htpasswd_password" "web-htpasswd-secret" {
  password = random_password.web-htpasswd-secret.result
  salt     = substr(sha512(random_password.web-htpasswd-secret.result), 0, 8)
}

// Save shared secret to Secret Manager
resource "google_secret_manager_secret" "turn_secret" {
  project   = var.project_id
  secret_id = "selkies-turn-shared-secret"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "turn_secret" {
  secret      = google_secret_manager_secret.turn_secret.id
  secret_data = random_password.turn-shared-secret.result
}

// Save htpasswd value to Secret Manager
resource "google_secret_manager_secret" "turn_htpasswd" {
  project   = var.project_id
  secret_id = "selkies-turn-htpasswd"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "turn_htpasswd" {
  secret      = google_secret_manager_secret.turn_htpasswd.id
  secret_data = "selkies:${htpasswd_password.web-htpasswd-secret.apr1}"
}