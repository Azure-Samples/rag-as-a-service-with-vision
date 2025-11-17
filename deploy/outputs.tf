

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "managed_identity_client_id" {
  description = "Client ID of the managed identity"
  value       = azurerm_user_assigned_identity.main.client_id
}

output "managed_identity_principal_id" {
  description = "Principal ID of the managed identity"
  value       = azurerm_user_assigned_identity.main.principal_id
}

output "computer_vision_endpoint" {
  description = "Azure Computer Vision endpoint"
  value       = azurerm_cognitive_account.computer_vision.endpoint
}

output "computer_vision_name" {
  description = "Azure Computer Vision service name"
  value       = azurerm_cognitive_account.computer_vision.name
}

output "cosmos_db_uri" {
  description = "Cosmos DB account URI"
  value       = azurerm_cosmosdb_account.main.endpoint
}

output "cosmos_account_name" {
  description = "Cosmos DB account name"
  value       = azurerm_cosmosdb_account.main.name
}

output "cosmos_database_name" {
  description = "Cosmos DB database name"
  value       = azurerm_cosmosdb_sql_database.main.name
}

output "cosmos_documents_container" {
  description = "Cosmos DB documents container name"
  value       = azurerm_cosmosdb_sql_container.documents.name
}

output "cosmos_enrichment_container" {
  description = "Cosmos DB enrichment container name"
  value       = azurerm_cosmosdb_sql_container.enrichment.name
}

output "search_endpoint" {
  description = "Azure Cognitive Search endpoint (integrated with AI Foundry)"
  value       = "https://${azurerm_search_service.main.name}.search.windows.net"
}

output "search_service_name" {
  description = "Azure Cognitive Search service name"
  value       = azurerm_search_service.main.name
}

output "ai_foundry_hub_name" {
  description = "AI Foundry hub name (Cognitive Services account)"
  value       = azapi_resource.ai_foundry.name
}

output "ai_foundry_project_name" {
  description = "AI Foundry project name"
  value       = azapi_resource.ai_foundry_project.name
}

output "ai_foundry_endpoint" {
  description = "AI Foundry endpoint for API access"
  value       = "https://${var.ai_foundry_project_name}.cognitiveservices.azure.com/"
}

output "model_deployments" {
  description = "Deployed AI models and their details"
  value = {
    for name, deployment in azurerm_cognitive_deployment.model_deployments : name => {
      name  = deployment.name
      model = deployment.model[0]
      scale = deployment.scale[0]
    }
  }
}

output "deployed_model_names" {
  description = "List of deployed model names"
  value       = [for deployment in azurerm_cognitive_deployment.model_deployments : deployment.name]
}

output "text_embedding_3_large" {
  value = {
    format  = "OpenAI"
    name    = "text-embedding-3-large"
    version = "1"
  }
  description = "Text embedding 3 large model"
}

output "gpt_4o" {
  value = {
    format  = "OpenAI"
    name    = "gpt-4o"
    version = "2024-11-20"
  }
  description = "GPT-4o model"
}

output "gpt_41" {
  value = {
    format  = "OpenAI"
    name    = "gpt-4.1"
    version = "2025-04-14"
  }
  description = "GPT-4.1 model"
}