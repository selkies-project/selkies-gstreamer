variable project_id {}
variable name {}

variable service_account {
  # If not specified, will create: selkies-turn@${var.project_id}.iam.gserviceaccount.com
  default = ""
}