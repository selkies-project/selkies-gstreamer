output image {
  value = local.image
}

output service_id {
  value = google_cloud_run_service.turn-web.id
}

output endpoint {
  value = element(google_cloud_run_service.turn-web.status[*].url, 0)
}