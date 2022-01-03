data "terraform_remote_state" "base" {
  backend = "gcs"
  config = {
    bucket = "${var.project_id}-${var.name}-tf-state"
    prefix = var.name
  }
  workspace = "base"
}
