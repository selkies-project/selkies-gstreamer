output "project_id" {
  description = "Project ID"
  value       = var.project_id
}

output "region" {
  description = "Region"
  value       = var.region
}

output turn_secret_id {
  description = "Secret Manager Secret ID containing the coTURN shared secret"
  value       = google_secret_manager_secret.turn_secret.id
}

output turn_node_ips {
  value = [for x in data.google_compute_instance.turn-cos-nodes : x.network_interface[0].access_config[0].nat_ip]
}