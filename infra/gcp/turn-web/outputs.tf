output image {
  value = data.google_container_registry_image.coturn-web.image_url
}

output service_id {
  value = google_cloud_run_service.turn-web.id
}

output endpoint {
  value = element(google_cloud_run_service.turn-web.status[*].url, 0)
}