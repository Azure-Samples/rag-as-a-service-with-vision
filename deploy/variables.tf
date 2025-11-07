# Resource Group Configuration
variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-rag-vision-service"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "West US 2"
}

# Managed Identity Configuration
variable "managed_identity_name" {
  description = "Name of the user managed identity to create"
  type        = string
  default     = "mi-rag-vision-service"
}

# App Service Configuration
variable "app_service_plan_name" {
  description = "Name of the App Service Plan"
  type        = string
  default     = "asp-rag-vision-service"
}

variable "app_service_name" {
  description = "Name of the App Service"
  type        = string
  default     = "app-rag-vision-service"
}

# Cosmos DB Configuration
variable "cosmos_account_name" {
  description = "Name of the Cosmos DB account"
  type        = string
  default     = "cosmos-rag-vision-service"
}

variable "cosmos_database_name" {
  description = "Cosmos DB database name"
  type        = string
  default     = "rag-vision-db"
}

variable "cosmos_container_name" {
  description = "Cosmos DB container name"
  type        = string
  default     = "rag-documents"
}

variable "cosmos_enrichment_container" {
  description = "Cosmos DB enrichment container name"
  type        = string
  default     = "enrichment-cache"
}

# Azure OpenAI Configuration
variable "azure_openai_endpoint" {
  description = "Azure OpenAI endpoint"
  type        = string
  default     = "https://cog-standard-xa2s6.cognitiveservices.azure.com/"
}

variable "azure_openai_api_version" {
  description = "Azure OpenAI API version"
  type        = string
  default     = "2025-03-01-preview"
}

variable "azure_mllm_deployment_model" {
  description = "Azure OpenAI deployment model name"
  type        = string
  default     = "gpt-4o"
}

# Azure AI Foundry Configuration
variable "azure_ai_foundry_endpoint" {
  description = "Azure AI Foundry endpoint"
  type        = string
  default     = "https://your-foundry-endpoint.inference.ml.azure.com"
}

variable "azure_ai_foundry_project_name" {
  description = "Azure AI Foundry project name"
  type        = string
  default     = "your-project-name"
}

variable "azure_ai_foundry_deployment_name" {
  description = "Azure AI Foundry deployment name"
  type        = string
  default     = "gpt-4o"
}

variable "azure_ai_foundry_api_version" {
  description = "Azure AI Foundry API version"
  type        = string
  default     = "2024-05-01-preview"
}

# Azure Cognitive Search Configuration
variable "azure_search_endpoint" {
  description = "Azure Cognitive Search endpoint"
  type        = string
  default     = "https://srch-standard-xa2s6.search.windows.net"
}

# Azure Computer Vision Configuration
variable "computer_vision_name" {
  description = "Name of the Computer Vision service"
  type        = string
  default     = "cv-rag-vision-service"
}

variable "computer_vision_sku" {
  description = "SKU for Computer Vision service"
  type        = string
  default     = "S1"
}

# Azure Cognitive Search Configuration (integrated with AI Foundry)
variable "search_service_name" {
  description = "Name of the Azure Cognitive Search service"
  type        = string
  default     = "search-rag-vision-service"
}

variable "search_sku" {
  description = "SKU for Azure Cognitive Search service"
  type        = string
  default     = "standard"
}

# AI Foundry / Machine Learning Configuration
variable "ai_foundry_project_name" {
  description = "Name of the AI Foundry project (ML Workspace)"
  type        = string
  default     = "aifoundry-rag-vision-project"
}

variable "key_vault_name" {
  description = "Name of the Key Vault for AI Foundry"
  type        = string
  default     = "kv-rag-vision-service"
}

variable "storage_account_name" {
  description = "Name of the Storage Account for AI Foundry"
  type        = string
  default     = "stragvisionservice"
}

# Model Deployments Configuration
variable "model_deployments" {
  description = "List of AI model deployments to create"
  type = list(object({
    name       = string # Deployment name
    model_name = string # Actual model name
    format     = string
    version    = string
    sku = object({
      name     = string
      capacity = number
    })
  }))
  default = [
    {
      name       = "gpt-4o-deployment"
      model_name = "gpt-4o"
      format     = "OpenAI"
      version    = "2024-11-20"
      sku = {
        name     = "GlobalStandard"
        capacity = 10
      }
    },
    {
      name       = "gpt-4-deployment"
      model_name = "gpt-4"
      format     = "OpenAI"
      version    = "2025-03-01-preview"
      sku = {
        name     = "GlobalStandard"
        capacity = 10
      }
    },
    {
      name       = "text-embedding-deployment"
      model_name = "text-embedding-3-large"
      format     = "OpenAI"
      version    = "1"
      sku = {
        name     = "GlobalStandard"
        capacity = 30
      }
    }
  ]
}