data "template_file" "cloud-config" {
  template = file("${path.module}/assets/cloud-config.yaml")

  vars = {
    custom_var    = var.cloud_init_custom_var
    instance_name = "${var.name}"
  }
}

resource "google_compute_instance_template" "default" {
  name_prefix  = "${var.name}-"
  project      = var.project_id
  machine_type = var.machine_type
  labels       = {}
  tags         = var.vm_tags
  region       = var.region

  scheduling {
    automatic_restart   = false
    on_host_maintenance = var.preemptible ? "TERMINATE" : "MIGRATE"
    preemptible         = var.preemptible
  }

  disk {
    source_image = "cos-cloud/cos-stable"
    auto_delete  = true
    boot         = true
    disk_size_gb = var.disk_size_gb
  }

  service_account {
    email  = var.service_account
    scopes = var.scopes
  }

  can_ip_forward = false

  network_interface {
    subnetwork = var.subnetwork
    network_ip = ""
    access_config {}
  }

  metadata = {
    google-logging-enabled    = var.stackdriver_logging
    google-monitoring-enabled = var.stackdriver_monitoring
    user-data                 = data.template_file.cloud-config.rendered
  }

  lifecycle {
    create_before_destroy = "true"
  }
}

module "mig" {
  source                    = "terraform-google-modules/vm/google//modules/mig"
  version                   = "~> 7.1.0"
  project_id                = var.project_id
  instance_template         = google_compute_instance_template.default.self_link
  subnetwork                = var.subnetwork
  region                    = var.region
  distribution_policy_zones = var.zones
  hostname                  = var.name
  autoscaling_enabled       = false
  target_size               = var.instance_count

  named_ports = [
    {
      name = "turn"
      port = 3478
    }
  ]
}
