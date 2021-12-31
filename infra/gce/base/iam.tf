resource "google_service_account" "turn_service_account" {
  count        = length(var.service_account) == 0 ? 1 : 0
  project      = var.project_id
  account_id   = "selkies-turn"
  display_name = "Selkies TURN server"
  depends_on   = [google_project_service.iam]
}

locals {
  sa_project = element(google_service_account.turn_service_account[*].project, 0)
  sa_email   = element(google_service_account.turn_service_account[*].email, 0)
}

resource "google_project_iam_member" "turn_service_account-log_writer" {
  count   = length(var.service_account) == 0 ? 1 : 0
  project = local.sa_project
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${local.sa_email}"
}

resource "google_project_iam_member" "turn_service_account-metric_writer" {
  count   = length(var.service_account) == 0 ? 1 : 0
  project = local.sa_project
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${local.sa_email}"
}

data "google_project" "project" {
  project_id = var.project_id
}

resource "google_project_iam_member" "cloud-run-compute-viewer" {
  project = var.project_id
  role    = "roles/compute.viewer"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}