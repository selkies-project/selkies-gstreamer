locals {
  gcp_regions = {
    "asia-east1"              = 0,  # Changhua County, Taiwan, APAC
    "asia-east2"              = 1,  # Hong Kong, APAC
    "asia-northeast1"         = 2,  # Tokyo, Japan, APAC
    "asia-northeast2"         = 3,  # Osaka, Japan, APAC
    "asia-northeast3"         = 4,  # Seoul, South Korea, APAC
    "asia-south1"             = 5,  # Mumbai, India APAC
    "asia-south2"             = 6,  # Delhi, India APAC
    "asia-southeast1"         = 7,  # Jurong West, Singapore, APAC
    "asia-southeast2"         = 8,  # Jakarta, Indonesia, APAC
    "australia-southeast1"    = 9,  # Sydney, Australia, APAC
    "australia-southeast2"    = 10, # Melbourne, Australia, APAC
    "APAC-TBD1"               = 11, # TBD
    "APAC-TBD2"               = 12, # TBD
    "APAC-TBD3"               = 13, # TBD
    "APAC-TBD4"               = 14, # TBD
    "APAC-TBD5"               = 15, # TBD
    "APAC-TBD6"               = 16, # TBD
    "APAC-TBD7"               = 17, # TBD
    "APAC-TBD8"               = 18, # TBD
    "APAC-TBD9"               = 19, # TBD
    "APAC-TBD10"              = 20, # TBD
    "europe-central2"         = 21, # Warsaw, Poland, Europe
    "europe-north1"           = 22, # Hamina, Finland, Europe
    "europe-west1"            = 23, # St. Ghislain, Belgium, Europe
    "europe-west2"            = 24, # London, England, Europe
    "europe-west3"            = 25, # Frankfurt, Germany Europe
    "europe-west4"            = 26, # Eemshaven, Netherlands, Europe
    "europe-west6"            = 27, # Zurich, Switzerland, Europe
    "EMEA-TBD1"               = 28, # TBD
    "EMEA-TBD2"               = 29, # TBD
    "EMEA-TBD3"               = 30, # TBD
    "EMEA-TBD4"               = 31, # TBD
    "EMEA-TBD5"               = 32, # TBD
    "EMEA-TBD6"               = 33, # TBD
    "EMEA-TBD7"               = 34, # TBD
    "EMEA-TBD8"               = 35, # TBD
    "northamerica-northeast1" = 36, # Montreal, Quebec, North America
    "NorthAm-TBD1"            = 37, # TBD
    "NorthAm-TBD2"            = 38, # TBD
    "NorthAm-TBD3"            = 39, # TBD
    "NorthAm-TBD4"            = 40, # TBD
    "southamerica-east1"      = 41, # Osasco, Sao Paulo, Brazil, South America
    "SouthAm-TBD1"            = 42, # TBD
    "SouthAm-TBD2"            = 43, # TBD
    "SouthAm-TBD3"            = 44, # TBD
    "SouthAm-TBD4"            = 45, # TBD
    "us-central1"             = 46, # Council Bluffs, Iowa, North America
    "us-east1"                = 47, # Moncks Corner, South Carolina, North America
    "us-east4"                = 48, # Ashburn, Virginia, North America
    "us-west1"                = 49, # The Dalles, Oregon, North America
    "us-west2"                = 50, # Los Angeles, California, North America
    "us-west3"                = 51, # Salt Lake City, Utah, North America
    "us-west4"                = 52, # Las Vegas, Nevada, North America
    "USA-TBD1"                = 53, # TBD
    "USA-TBD2"                = 54, # TBD
    "USA-TBD3"                = 55, # TBD
    "USA-TBD4"                = 56, # TBD
    "USA-TBD5"                = 57, # TBD
    "USA-TBD6"                = 58, # TBD
    "USA-TBD7"                = 59, # TBD
  }

  // Map of regions to zones that TURN instances will be deployed to.
  node_zones = {
    "us-west1"                = ["us-west1-a"],
    "us-west2"                = ["us-west2-b"],
    "us-central1"             = ["us-central1-a"],
    "us-east1"                = ["us-east1-c"],
    "us-east4"                = ["us-east4-a"],
    "northamerica-northeast1" = ["northamerica-northeast1-a"],
    "southamerica-east1"      = ["southamerica-east1-c"],
    "europe-west1"            = ["europe-west1-b"],
    "europe-west2"            = ["europe-west2-a"],
    "europe-west3"            = ["europe-west3-b"],
    "europe-west4"            = ["europe-west4-b"],
    "asia-east1"              = ["asia-east1-a"],
    "asia-northeast1"         = ["asia-northeast1-a"],
    "asia-northeast3"         = ["asia-northeast3-b"],
    "asia-south1"             = ["asia-south1-a"],
    "asia-southeast1"         = ["asia-southeast1-b"],
    "australia-southeast1"    = ["australia-southeast1-a"],
  }

  // Default subnet values computed from region indices.
  default_ip_cidr_range = "10.${2 + lookup(local.gcp_regions, var.region)}.0.0/16"
}
