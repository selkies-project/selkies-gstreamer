resource "google_compute_network" "selkies" {
  name                    = var.name
  auto_create_subnetworks = false
  depends_on = [
    google_project_service.compute
  ]
}

resource "google_compute_firewall" "turn" {
  name = "selkies-turn"
  network = replace(
    google_compute_network.selkies.self_link,
    "https://www.googleapis.com/compute/v1/",
    "",
  )

  allow {
    protocol = "tcp"
    ports    = ["3478", "25000-25100"]
  }

  allow {
    protocol = "udp"
    ports    = ["3478", "25000-25100"]
  }

  target_tags   = ["selkies-turn"]
  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "iap" {
  name = "${var.name}-allow-ingress-from-iap"
  network = replace(
    google_compute_network.selkies.self_link,
    "https://www.googleapis.com/compute/v1/",
    "",
  )

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["35.235.240.0/20"]
}