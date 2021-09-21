// Key used to sign HMAC credentials, must be used by all instances.
resource "random_password" "turn-shared-secret" {
  length  = 16
  special = false
}