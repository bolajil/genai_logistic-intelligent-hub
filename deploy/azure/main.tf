# GLIH Azure Deployment - AKS + Azure Database + Azure Cache
terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }

  backend "azurerm" {
    resource_group_name  = "glih-terraform-state"
    storage_account_name = "glihtfstate"
    container_name       = "tfstate"
    key                  = "azure/terraform.tfstate"
  }
}

provider "azurerm" {
  features {}
}

# ============================================================
# Variables
# ============================================================
variable "location" {
  default = "East US"
}

variable "environment" {
  default = "production"
}

variable "db_sku" {
  default = "GP_Standard_D2s_v3"
}

variable "db_password" {
  sensitive = true
}

# ============================================================
# Resource Group
# ============================================================
resource "azurerm_resource_group" "glih" {
  name     = "glih-${var.environment}"
  location = var.location

  tags = {
    Project     = "GLIH"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# ============================================================
# Virtual Network
# ============================================================
resource "azurerm_virtual_network" "glih" {
  name                = "glih-vnet"
  address_space       = ["10.0.0.0/8"]
  location            = azurerm_resource_group.glih.location
  resource_group_name = azurerm_resource_group.glih.name
}

resource "azurerm_subnet" "aks" {
  name                 = "aks-subnet"
  resource_group_name  = azurerm_resource_group.glih.name
  virtual_network_name = azurerm_virtual_network.glih.name
  address_prefixes     = ["10.240.0.0/16"]
}

resource "azurerm_subnet" "db" {
  name                 = "db-subnet"
  resource_group_name  = azurerm_resource_group.glih.name
  virtual_network_name = azurerm_virtual_network.glih.name
  address_prefixes     = ["10.241.0.0/24"]

  delegation {
    name = "postgresql"
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

# ============================================================
# AKS Cluster
# ============================================================
resource "azurerm_kubernetes_cluster" "glih" {
  name                = "glih-aks"
  location            = azurerm_resource_group.glih.location
  resource_group_name = azurerm_resource_group.glih.name
  dns_prefix          = "glih"

  default_node_pool {
    name           = "default"
    node_count     = 3
    vm_size        = "Standard_D2s_v3"
    vnet_subnet_id = azurerm_subnet.aks.id
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    load_balancer_sku = "standard"
  }
}

# ============================================================
# Azure Database for PostgreSQL Flexible Server
# ============================================================
resource "azurerm_private_dns_zone" "postgres" {
  name                = "glih.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.glih.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "glih-postgres-link"
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  resource_group_name   = azurerm_resource_group.glih.name
  virtual_network_id    = azurerm_virtual_network.glih.id
}

resource "azurerm_postgresql_flexible_server" "glih" {
  name                   = "glih-postgres"
  resource_group_name    = azurerm_resource_group.glih.name
  location               = azurerm_resource_group.glih.location
  version                = "16"
  delegated_subnet_id    = azurerm_subnet.db.id
  private_dns_zone_id    = azurerm_private_dns_zone.postgres.id
  administrator_login    = "glih_admin"
  administrator_password = var.db_password
  storage_mb             = 32768
  sku_name               = var.db_sku

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

resource "azurerm_postgresql_flexible_server_database" "glih" {
  name      = "glih"
  server_id = azurerm_postgresql_flexible_server.glih.id
}

# ============================================================
# Azure Cache for Redis
# ============================================================
resource "azurerm_redis_cache" "glih" {
  name                = "glih-redis"
  location            = azurerm_resource_group.glih.location
  resource_group_name = azurerm_resource_group.glih.name
  capacity            = 1
  family              = "C"
  sku_name            = "Basic"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"
}

# ============================================================
# Azure Container Registry
# ============================================================
resource "azurerm_container_registry" "glih" {
  name                = "glihreg${var.environment}"
  resource_group_name = azurerm_resource_group.glih.name
  location            = azurerm_resource_group.glih.location
  sku                 = "Standard"
  admin_enabled       = true
}

# ============================================================
# Azure Key Vault — GLIH application secrets
# Stores JWT_SECRET, SENTRY_DSN, OPENAI_API_KEY, DATABASE_URL
# AKS pods access via Workload Identity + CSI secret store driver
# ============================================================
resource "azurerm_key_vault" "glih" {
  name                = "glih-kv-${var.environment}"
  location            = azurerm_resource_group.glih.location
  resource_group_name = azurerm_resource_group.glih.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  soft_delete_retention_days = var.environment == "production" ? 90 : 7
  purge_protection_enabled   = var.environment == "production"

  tags = {
    Project     = "GLIH"
    Environment = var.environment
  }
}

data "azurerm_client_config" "current" {}

# Secrets — values must be set manually after vault creation
resource "azurerm_key_vault_secret" "jwt_secret" {
  name         = "glih-jwt-secret"
  value        = "REPLACE_WITH_GENERATED_SECRET"  # python -c "import secrets; print(secrets.token_hex(32))"
  key_vault_id = azurerm_key_vault.glih.id

  lifecycle {
    ignore_changes = [value]  # Prevent Terraform overwriting manual updates
  }
}

resource "azurerm_key_vault_secret" "openai_key" {
  name         = "glih-openai-api-key"
  value        = "REPLACE_WITH_OPENAI_KEY"
  key_vault_id = azurerm_key_vault.glih.id

  lifecycle {
    ignore_changes = [value]
  }
}

resource "azurerm_key_vault_secret" "sentry_dsn" {
  name         = "glih-sentry-dsn"
  value        = "REPLACE_WITH_SENTRY_DSN"
  key_vault_id = azurerm_key_vault.glih.id

  lifecycle {
    ignore_changes = [value]
  }
}

# AKS managed identity access to Key Vault
resource "azurerm_user_assigned_identity" "glih_backend" {
  name                = "glih-backend-identity"
  resource_group_name = azurerm_resource_group.glih.name
  location            = azurerm_resource_group.glih.location
}

resource "azurerm_key_vault_access_policy" "glih_backend" {
  key_vault_id = azurerm_key_vault.glih.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_user_assigned_identity.glih_backend.principal_id

  secret_permissions = ["Get", "List"]
}

# ============================================================
# Storage Account for trucks.json persistence
# ============================================================
resource "azurerm_storage_account" "glih" {
  name                     = "glihdata${var.environment}"
  resource_group_name      = azurerm_resource_group.glih.name
  location                 = azurerm_resource_group.glih.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "fleet" {
  name                  = "fleet-data"
  storage_account_name  = azurerm_storage_account.glih.name
  container_access_type = "private"
}

# ============================================================
# Outputs
# ============================================================
output "aks_cluster_name" {
  value = azurerm_kubernetes_cluster.glih.name
}

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.glih.fqdn
}

output "redis_hostname" {
  value = azurerm_redis_cache.glih.hostname
}

output "acr_login_server" {
  value = azurerm_container_registry.glih.login_server
}

output "key_vault_uri" {
  value       = azurerm_key_vault.glih.vault_uri
  description = "Key Vault URI — reference secrets in AKS pod spec via CSI Secret Store driver"
}

output "backend_identity_client_id" {
  value       = azurerm_user_assigned_identity.glih_backend.client_id
  description = "Assign to AKS backend pod via azure.workload.identity/client-id annotation"
}
