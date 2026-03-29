# GLIH GCP Deployment - GKE Autopilot + Cloud SQL + Memorystore
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }

  backend "gcs" {
    bucket = "glih-terraform-state"
    prefix = "gcp/terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ============================================================
# Variables
# ============================================================
variable "project_id" {
  description = "GCP Project ID"
}

variable "region" {
  default = "us-central1"
}

variable "environment" {
  default = "production"
}

variable "db_tier" {
  default = "db-custom-2-4096"
}

variable "db_password" {
  sensitive = true
}

# ============================================================
# VPC Network
# ============================================================
resource "google_compute_network" "glih" {
  name                    = "glih-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "glih" {
  name          = "glih-subnet"
  ip_cidr_range = "10.0.0.0/20"
  region        = var.region
  network       = google_compute_network.glih.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.1.0.0/16"
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.2.0.0/20"
  }
}

# ============================================================
# GKE Autopilot Cluster
# ============================================================
resource "google_container_cluster" "glih" {
  name     = "glih-gke"
  location = var.region

  enable_autopilot = true

  network    = google_compute_network.glih.name
  subnetwork = google_compute_subnetwork.glih.name

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  release_channel {
    channel = "REGULAR"
  }

  deletion_protection = var.environment == "production"
}

# ============================================================
# Cloud SQL PostgreSQL
# ============================================================
resource "google_sql_database_instance" "glih" {
  name             = "glih-postgres"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier = var.db_tier

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.glih.id
    }

    backup_configuration {
      enabled            = true
      start_time         = "03:00"
      binary_log_enabled = false
    }
  }

  deletion_protection = var.environment == "production"
}

resource "google_sql_database" "glih" {
  name     = "glih"
  instance = google_sql_database_instance.glih.name
}

resource "google_sql_user" "glih" {
  name     = "glih_admin"
  instance = google_sql_database_instance.glih.name
  password = var.db_password
}

# ============================================================
# Memorystore Redis
# ============================================================
resource "google_redis_instance" "glih" {
  name           = "glih-redis"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region

  authorized_network = google_compute_network.glih.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  redis_version = "REDIS_7_0"
}

# ============================================================
# Artifact Registry
# ============================================================
resource "google_artifact_registry_repository" "glih" {
  location      = var.region
  repository_id = "glih-images"
  format        = "DOCKER"
}

# ============================================================
# Cloud Storage for trucks.json persistence
# ============================================================
resource "google_storage_bucket" "glih_data" {
  name     = "${var.project_id}-glih-data"
  location = var.region

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }
}

# ============================================================
# GCP Secret Manager — GLIH application secrets
# Stores JWT_SECRET, SENTRY_DSN, OPENAI_API_KEY, DATABASE_URL
# Backend reads via Workload Identity + Secret Manager API
# ============================================================
resource "google_secret_manager_secret" "glih_jwt" {
  secret_id = "glih-jwt-secret-${var.environment}"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "glih_jwt" {
  secret      = google_secret_manager_secret.glih_jwt.id
  secret_data = "REPLACE_WITH_GENERATED_SECRET"  # python -c "import secrets; print(secrets.token_hex(32))"

  lifecycle {
    ignore_changes = [secret_data]  # Prevent Terraform overwriting manual updates
  }
}

resource "google_secret_manager_secret" "glih_openai" {
  secret_id = "glih-openai-key-${var.environment}"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "glih_sentry" {
  secret_id = "glih-sentry-dsn-${var.environment}"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "glih_admin_password" {
  secret_id = "glih-admin-password-${var.environment}"
  replication { auto {} }
}

resource "google_secret_manager_secret_version" "glih_admin_password" {
  secret      = google_secret_manager_secret.glih_admin_password.id
  secret_data = "REPLACE_WITH_STRONG_PASSWORD"
  lifecycle { ignore_changes = [secret_data] }
}

resource "google_secret_manager_secret" "glih_dispatcher_password" {
  secret_id = "glih-dispatcher-password-${var.environment}"
  replication { auto {} }
}

resource "google_secret_manager_secret_version" "glih_dispatcher_password" {
  secret      = google_secret_manager_secret.glih_dispatcher_password.id
  secret_data = "REPLACE_WITH_STRONG_PASSWORD"
  lifecycle { ignore_changes = [secret_data] }
}

resource "google_secret_manager_secret" "glih_dispatcher_admin_password" {
  secret_id = "glih-dispatcher-admin-password-${var.environment}"
  replication { auto {} }
}

resource "google_secret_manager_secret_version" "glih_dispatcher_admin_password" {
  secret      = google_secret_manager_secret.glih_dispatcher_admin_password.id
  secret_data = "REPLACE_WITH_STRONG_PASSWORD"
  lifecycle { ignore_changes = [secret_data] }
}

# Service account for GKE workloads to access secrets
resource "google_service_account" "glih_backend" {
  account_id   = "glih-backend-${var.environment}"
  display_name = "GLIH Backend Service Account"
}

resource "google_secret_manager_secret_iam_member" "jwt_access" {
  secret_id = google_secret_manager_secret.glih_jwt.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.glih_backend.email}"
}

resource "google_secret_manager_secret_iam_member" "openai_access" {
  secret_id = google_secret_manager_secret.glih_openai.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.glih_backend.email}"
}

# ============================================================
# Outputs
# ============================================================
output "gke_cluster_name" {
  value = google_container_cluster.glih.name
}

output "cloudsql_connection_name" {
  value = google_sql_database_instance.glih.connection_name
}

output "redis_host" {
  value = google_redis_instance.glih.host
}

output "artifact_registry_url" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.glih.repository_id}"
}

output "backend_service_account" {
  value       = google_service_account.glih_backend.email
  description = "Use for GKE Workload Identity — annotate backend pod service account with this"
}

output "jwt_secret_name" {
  value       = google_secret_manager_secret.glih_jwt.name
  description = "Reference in GKE pod spec as environment variable from Secret Manager"
}
