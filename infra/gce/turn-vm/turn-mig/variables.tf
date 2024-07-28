variable "project_id" {
  description = "Project id where the instances will be created."
  type        = string
}

variable "region" {
  description = "Region for external addresses."
  type        = string
}

variable "zones" {
  description = "Distribution policy zones"
  type        = list(string)
  default     = []
}

variable "subnetwork" {
  description = "Self link of the VPC subnet to use for the internal interface."
  type        = string
}

variable "instance_count" {
  description = "Number of instances to create."
  type        = number
  default     = 1
}

variable "machine_type" {
  description = "Instance machine type."
  type        = string
  default     = "e2-standard-2"
}

variable "scopes" {
  description = "Instance scopes."
  type        = list(string)
  default = [
    "https://www.googleapis.com/auth/devstorage.read_only",
    "https://www.googleapis.com/auth/logging.write",
    "https://www.googleapis.com/auth/monitoring.write",
    "https://www.googleapis.com/auth/pubsub",
    "https://www.googleapis.com/auth/service.management.readonly",
    "https://www.googleapis.com/auth/servicecontrol",
    "https://www.googleapis.com/auth/trace.append",
  ]
}

variable "service_account" {
  description = "Instance service account."
  type        = string
  default     = ""
}

variable "name" {
  description = "name used in prefix of instances"
  default     = "turn"
}

variable "disk_size_gb" {
  description = "Size of the boot disk."
  type        = number
  default     = 10
}

variable "disk_type" {
  description = "Type of boot disk"
  default     = "pd-standard"
}

variable "vm_tags" {
  description = "Additional network tags for the instances."
  type        = list(string)
  default = [
    "selkies-turn"
  ]
}

variable "preemptible" {
  description = "Make the instance preemptible"
  default     = false
}

variable "stackdriver_logging" {
  description = "Enable the Stackdriver logging agent."
  type        = bool
  default     = true
}

variable "stackdriver_monitoring" {
  description = "Enable the Stackdriver monitoring agent."
  type        = bool
  default     = false
}

variable "allow_stopping_for_update" {
  description = "Allow stopping the instance for specific Terraform changes."
  type        = bool
  default     = false
}

variable "cloud_init_custom_var" {
  description = "String passed in to the cloud-config template as custom variable."
  type        = string
  default     = ""
}