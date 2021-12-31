terraform {
  backend "gcs" {}
  required_version = ">= 0.12"
  required_providers {
    google   = "~> 3.51, <4.0.0"
    template = "~> 2.1"
  }
}
