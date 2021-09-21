output turn_shared_secret {
  value     = random_password.turn-shared-secret.result
  sensitive = true
}

output service_account {
  value = length(var.service_account) == 0 ? element(google_service_account.turn_service_account.*.email, 0) : var.service_account
}