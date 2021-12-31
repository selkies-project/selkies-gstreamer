output service_account {
  value = length(var.service_account) == 0 ? element(google_service_account.turn_service_account.*.email, 0) : var.service_account
}

output selkies_htpasswd {
  value = random_password.web-htpasswd-secret.result
  sensitive = true
}

output selkies_htpasswd_instructions {
  value = "To get the value of the htpasswd secret run this command: gsutil cat gs://${var.project_id}-selkies-tf-state/selkies/base.tfstate | jq -r .outputs.selkies_htpasswd.value"
}