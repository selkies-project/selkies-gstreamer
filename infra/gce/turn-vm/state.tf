data "terraform_remote_state" "base" {
  backend = "gcs"
  config = {
    bucket = "${var.project_id}-${var.name}-tf-state"
    prefix = var.name
  }
  workspace = "base"
}

data "terraform_remote_state" "turn-web" {
  backend = "gcs"
  config = {
    bucket = "${var.project_id}-${var.name}-tf-state"
    prefix = var.name
  }
  workspace = "turn-web-${var.turn_web_region}"
}
