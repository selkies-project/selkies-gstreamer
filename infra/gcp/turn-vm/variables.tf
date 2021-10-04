variable project_id {}
variable region {}

variable zones {
  type    = list
  default = []
}

variable name {
  default = "selkies"
}

variable ip_cidr_range {
  // CIDR range for subnetwork, auto-created from locals if empty
  default = ""
}

variable turn_pool_machine_type {
  default = "e2-highcpu-2"
}
variable turn_pool_disk_size_gb {
  default = 10
}
variable turn_pool_disk_type {
  default = "pd-standard"
}
variable turn_pool_instance_count {
  default = 1
}
variable turn_pool_preemptive_nodes {
  default = false
}
variable coturn_image {
  default = "ghcr.io/selkies-project/selkies-gstreamer/coturn:latest"
}
variable turn_realm {
  // realm to return for TURN host. If not set, will lookup the endpoing for the turn-web Cloud run service.
  default = ""
}

variable turn_web_region {
  default = "us-west1"
}