data "google_compute_network" "selkies" {
  name = var.name
}

resource "google_compute_subnetwork" "selkies" {
  name          = "${var.name}-${var.region}"
  ip_cidr_range = length(var.ip_cidr_range) == 0 ? local.default_ip_cidr_range : var.ip_cidr_range
  region        = var.region
  network       = data.google_compute_network.selkies.self_link
}
