terraform {
  backend "gcs" {}
  required_version = ">= 0.12"
  required_providers {
    google   = "~> 3.51, <4.0.0"
    template = "~> 2.1"
    random   = "~> 2.2"
    docker = {
      source  = "kreuzwerker/docker"
      version = "2.15.0"
    }
  }
}
