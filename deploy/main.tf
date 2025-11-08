# RAG-as-a-Service with Vision - Terraform Configuration

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.117"
    }
    azapi = {
      source  = "Azure/azapi"
      version = "~>1.5"
    }
    time = {
      source  = "hashicorp/time"
      version = "~>0.9"
    }
  }
  required_version = ">= 1.3"
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location
}

# User Managed Identity
resource "azurerm_user_assigned_identity" "main" {
  name                = var.managed_identity_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
}

# Azure Computer Vision
resource "azurerm_cognitive_account" "computer_vision" {
  name                = var.computer_vision_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "ComputerVision"
  sku_name           = var.computer_vision_sku
  
  tags = {
    Environment = "Production"
    Service     = "RAG-Vision"
  }
}

# Cognitive Services User Role Assignment for User Managed Identity
resource "azurerm_role_assignment" "computer_vision_user" {
  scope                = azurerm_cognitive_account.computer_vision.id
  role_definition_name = "Cognitive Services User"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# Cosmos DB Account
resource "azurerm_cosmosdb_account" "main" {
  name                = var.cosmos_account_name
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }

  tags = {
    Environment = "Production"
    Service     = "RAG-Vision"
  }
}

# Cosmos DB Database
resource "azurerm_cosmosdb_sql_database" "main" {
  name                = var.cosmos_database_name
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
}

# Cosmos DB Container for RAG Documents
resource "azurerm_cosmosdb_sql_container" "documents" {
  name                = var.cosmos_container_name
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_paths = ["/id"]
  throughput          = 400

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }
  }
}

# Cosmos DB Container for Enrichment Cache
resource "azurerm_cosmosdb_sql_container" "enrichment" {
  name                = var.cosmos_enrichment_container
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
  database_name       = azurerm_cosmosdb_sql_database.main.name
  partition_key_paths = ["/key"]
  throughput          = 400

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }
  }
}

# Azure Cognitive Search (integrated with AI Foundry)
resource "azurerm_search_service" "main" {
  name                = var.search_service_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.search_sku
  replica_count       = 1
  partition_count     = 1

  # Enable Azure AD authentication (disable API key only mode)
  local_authentication_enabled = true
  authentication_failure_mode  = "http403"

  tags = {
    Environment = "Production"
    Service     = "RAG-Vision"
  }
}

# Search Service Contributor Role Assignment for User Managed Identity
resource "azurerm_role_assignment" "search_service_contributor" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Service Contributor"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# Search Index Data Contributor Role Assignment for Current User
resource "azurerm_role_assignment" "search_index_data_contributor_current" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# Search Index Data Reader Role Assignment for Current User
resource "azurerm_role_assignment" "search_index_data_reader_current" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Reader"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# AI Foundry Hub (Cognitive Services Account)
resource "azapi_resource" "ai_foundry" {
  type                      = "Microsoft.CognitiveServices/accounts@2025-06-01"
  name                      = var.ai_foundry_project_name
  parent_id                 = azurerm_resource_group.main.id
  location                  = azurerm_resource_group.main.location
  schema_validation_enabled = false

  body = {
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      disableLocalAuth = false
      allowProjectManagement = true
      customSubDomainName = var.ai_foundry_project_name
      publicNetworkAccess = "Enabled"
    }
  }

  tags = {
    Environment = "Production"
    Service     = "RAG-Vision"
  }

  depends_on = [time_sleep.wait_before_purge]
}

# Cognitive Services User Role Assignment for AI Foundry Hub
resource "azurerm_role_assignment" "ai_foundry_user" {
  scope                = azapi_resource.ai_foundry.id
  role_definition_name = "Cognitive Services User"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# Cognitive Services OpenAI User Role Assignment for AI Foundry Hub (for data plane operations) - Managed Identity
resource "azurerm_role_assignment" "ai_foundry_openai_user" {
  scope                = azapi_resource.ai_foundry.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# Cognitive Services Contributor Role Assignment for AI Foundry Hub
resource "azurerm_role_assignment" "ai_foundry_contributor" {
  scope                = azapi_resource.ai_foundry.id
  role_definition_name = "Cognitive Services Contributor"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# Custom role definition for OpenAI data plane operations
resource "azurerm_role_definition" "openai_data_operations" {
  name        = "OpenAI Data Operations - RAG Vision"
  scope       = azapi_resource.ai_foundry.id
  description = "Custom role for OpenAI data plane operations including embeddings and chat completions"

  permissions {
    actions = [
      "Microsoft.CognitiveServices/accounts/read"
    ]
    data_actions = [
      "Microsoft.CognitiveServices/accounts/OpenAI/deployments/embeddings/action",
      "Microsoft.CognitiveServices/accounts/OpenAI/deployments/chat/completions/action",
      "Microsoft.CognitiveServices/accounts/OpenAI/deployments/completions/action",
      "Microsoft.CognitiveServices/accounts/AIServices/agents/read",
      "Microsoft.CognitiveServices/accounts/AIServices/*/read",
      "Microsoft.CognitiveServices/accounts/OpenAI/*/read"
    ]
  }

  assignable_scopes = [
    azapi_resource.ai_foundry.id
  ]
}

# Assign custom OpenAI role to managed identity
resource "azurerm_role_assignment" "ai_foundry_openai_custom_managed" {
  scope              = azapi_resource.ai_foundry.id
  role_definition_id = azurerm_role_definition.openai_data_operations.role_definition_resource_id
  principal_id       = azurerm_user_assigned_identity.main.principal_id
}

# Development Environment: Add OpenAI permissions to current user since managed identity is not available in dev containers
# Cognitive Services OpenAI User Role Assignment for Current User
resource "azurerm_role_assignment" "ai_foundry_openai_user_current" {
  scope                = azapi_resource.ai_foundry.id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Cognitive Services Contributor Role Assignment for Current User
resource "azurerm_role_assignment" "ai_foundry_contributor_current" {
  scope                = azapi_resource.ai_foundry.id
  role_definition_name = "Cognitive Services Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Assign custom OpenAI role to current user
resource "azurerm_role_assignment" "ai_foundry_openai_custom_current" {
  scope              = azapi_resource.ai_foundry.id
  role_definition_id = azurerm_role_definition.openai_data_operations.role_definition_resource_id
  principal_id       = data.azurerm_client_config.current.object_id
}

# Development Environment: Add Computer Vision permissions to current user
# Cognitive Services User Role Assignment for Current User (Computer Vision)
resource "azurerm_role_assignment" "computer_vision_user_current" {
  scope                = azurerm_cognitive_account.computer_vision.id
  role_definition_name = "Cognitive Services User"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Development Environment: Add Azure Search permissions to current user
# Search Service Contributor Role Assignment for Current User
resource "azurerm_role_assignment" "search_service_contributor_current" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Service Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Search Index Data Contributor Role Assignment for Current User
resource "azurerm_role_assignment" "search_index_data_contributor_current_user" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Search Index Data Reader Role Assignment for Current User
resource "azurerm_role_assignment" "search_index_data_reader_current_user" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Reader"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Optional timed delay after deletion before purge to avoid 404 (soft-delete not yet visible)
resource "time_sleep" "wait_before_purge" {
  destroy_duration = "60s"

  depends_on = [azapi_resource_action.purge_ai_foundry]
}

# Purge soft-deleted Cognitive account AFTER account deletion (and optional delay).
# By having the module depend on this action, Terraform will destroy the module (account) first, then issue the purge.
resource "azapi_resource_action" "purge_ai_foundry" {
  method      = "DELETE"
  resource_id = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/providers/Microsoft.CognitiveServices/locations/${azurerm_resource_group.main.location}/resourceGroups/${azurerm_resource_group.main.name}/deletedAccounts/${var.ai_foundry_project_name}"
  type        = "Microsoft.Resources/resourceGroups/deletedAccounts@2021-04-30"
  when        = "destroy"
}

# AI Foundry Project
resource "azapi_resource" "ai_foundry_project" {
  depends_on = [azapi_resource.ai_foundry]

  type                      = "Microsoft.CognitiveServices/accounts/projects@2025-06-01"
  name                      = "${var.ai_foundry_project_name}-project"
  parent_id                 = azapi_resource.ai_foundry.id
  location                  = azurerm_resource_group.main.location
  schema_validation_enabled = false

  body = {
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      displayName = "RAG Vision Project"
      description = "AI Foundry project for RAG-as-a-Service with Vision"
    }
  }

  response_export_values = [
    "identity.principalId",
    "properties.internalId"
  ]
}

# AI Foundry will manage its own storage internally

# For each configured model, create a deployment
locals {
  model_deployments = {
    for model in var.model_deployments : model.name => model
  }
}

# Model Deployments for AI Foundry
resource "azurerm_cognitive_deployment" "model_deployments" {
  for_each = local.model_deployments

  depends_on = [
    azapi_resource.ai_foundry_project
  ]

  name                 = each.value.name
  cognitive_account_id = azapi_resource.ai_foundry.id

  model {
    format  = each.value.format
    name    = each.value.model_name
    version = each.value.version
  }

  scale {
    type     = each.value.sku.name
    capacity = each.value.sku.capacity
  }
}

# Cosmos DB SQL Role Assignment for User Managed Identity (Data access)
resource "azurerm_cosmosdb_sql_role_assignment" "main" {
  resource_group_name   = azurerm_resource_group.main.name
  account_name         = azurerm_cosmosdb_account.main.name
  role_definition_id   = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.main.name}/providers/Microsoft.DocumentDB/databaseAccounts/${azurerm_cosmosdb_account.main.name}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
  scope               = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.main.name}/providers/Microsoft.DocumentDB/databaseAccounts/${azurerm_cosmosdb_account.main.name}"
}

# Cosmos DB Operator Role Assignment for User Managed Identity (Full operational access)
resource "azurerm_role_assignment" "cosmos_operator" {
  scope                = azurerm_cosmosdb_account.main.id
  role_definition_name = "Cosmos DB Operator"
  principal_id         = azurerm_user_assigned_identity.main.principal_id
}

# Additional Cosmos DB Operator Role Assignment for current user/service context
resource "azurerm_role_assignment" "cosmos_operator_current_user" {
  scope                = azurerm_cosmosdb_account.main.id
  role_definition_name = "Cosmos DB Operator"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Additional Cosmos DB Account Reader Role Assignment for current user/service context
resource "azurerm_role_assignment" "cosmos_reader_current_user" {
  scope                = azurerm_cosmosdb_account.main.id
  role_definition_name = "Cosmos DB Account Reader Role"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Additional Cosmos DB SQL Data Contributor for current user/service context
resource "azurerm_cosmosdb_sql_role_assignment" "current_user" {
  resource_group_name   = azurerm_resource_group.main.name
  account_name         = azurerm_cosmosdb_account.main.name
  role_definition_id   = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.main.name}/providers/Microsoft.DocumentDB/databaseAccounts/${azurerm_cosmosdb_account.main.name}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002"
  principal_id         = data.azurerm_client_config.current.object_id
  scope               = "/subscriptions/${data.azurerm_client_config.current.subscription_id}/resourceGroups/${azurerm_resource_group.main.name}/providers/Microsoft.DocumentDB/databaseAccounts/${azurerm_cosmosdb_account.main.name}"
}

data "azurerm_client_config" "current" {}