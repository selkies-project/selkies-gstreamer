data "google_secret_manager_secret_version" "turn-shared-secret" {
  secret = "selkies-turn-shared-secret"
}

locals {
  coturn_image       = var.coturn_image
  turn_shared_secret = data.google_secret_manager_secret_version.turn-shared-secret.secret_data
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
  cloud_init_custom_var = "${local.turn_shared_secret},${var.turn_realm},${local.coturn_image},"
  vm_tags               = ["selkies-turn"]
}

data "google_compute_region_instance_group" "turn-cos-nodes" {
  self_link = replace(module.turn-cos-nodes.instance_group, "instanceGroupManagers", "instanceGroups")
}
