variable project_id {}
variable region {}
variable name {
  default = "selkies"
}
variable image_repo {
  default = "gcr.io/PROJECT_ID/selkies-gstreamer-coturn-web"
}
variable image_tag {
  default = "latest"
}
variable htpasswd_secret_name {
  default = "selkies-turn-htpasswd"
}
variable mig_disco_filter {
  default = "selkies-turn-.*-mig"
}