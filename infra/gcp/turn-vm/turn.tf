locals {
  coturn_image       = var.coturn_image
  turn_shared_secret = data.terraform_remote_state.base.outputs.turn_shared_secret

  // Default the REALM to the Cloud Endpoints DNS name
  turn_realm = length(var.turn_realm) == 0 ? data.terraform_remote_state.turn-web.outputs.endpoint : var.turn_realm
}

module "turn-cos-nodes" {
  source                = "./turn-mig"
  instance_count        = var.turn_pool_instance_count
  project_id            = var.project_id
  subnetwork            = google_compute_subnetwork.selkies.self_link
  machine_type          = var.turn_pool_machine_type
  preemptible           = var.turn_pool_preemptive_nodes
  region                = var.region
  zones                 = local.node_zones[var.region]
  name                  = "selkies-turn-${var.region}"
  disk_size_gb          = var.turn_pool_disk_size_gb
  disk_type             = var.turn_pool_disk_type
  scopes                = ["https://www.googleapis.com/auth/cloud-platform"]
  service_account       = data.terraform_remote_state.base.outputs.service_account
  cloud_init_custom_var = "${local.turn_shared_secret},${local.turn_realm},${local.coturn_image},"
  vm_tags               = ["selkies-turn"]
}

data "google_compute_region_instance_group" "turn-cos-nodes" {
  self_link = replace(module.turn-cos-nodes.instance_group, "instanceGroupManagers", "instanceGroups")
}

data "google_compute_instance" "turn-cos-nodes" {
  for_each  = toset(data.google_compute_region_instance_group.turn-cos-nodes.instances[*].instance)
  self_link = each.key
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
  secret_data = local.turn_shared_secret
}