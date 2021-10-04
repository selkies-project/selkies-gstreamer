variable project_id {}
variable region {}
variable name {
  default = "selkies"
}
variable image_tag {
  default = "latest"
}
variable image_digest {
  default = ""
}
variable htpasswd_secret_name {
  default = "selkies-turn-htpasswd"
}

variable mig_disco_filter {
  default = "selkies-turn-.*-mig"
}