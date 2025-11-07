# Terraform Deployment for RAG-as-a-Service with Vision

## Overview
This directory contains Terraform configuration for deploying the RAG-as-a-Service with Vision application to Azure.

## Files
- `main.tf` - Main Terraform configuration
- `variables.tf` - Variable definitions
- `outputs.tf` - Output definitions
- `terraform.tfvars.example` - Example configuration values

## Prerequisites
- Terraform installed
- Azure CLI installed and logged in (`az login`)
- Existing User Managed Identity
- Existing Cosmos DB account

## Quick Deployment

### 1. Configure Variables
```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your actual values
```

### 2. Initialize and Deploy
```bash
cd deploy
terraform init
terraform plan
terraform apply
```

### 3. Deploy Application Code
```bash
# After infrastructure is ready
az webapp up --name <app-service-name> --resource-group <resource-group-name> --src-path ../src/api
```

## Configuration

### Required Variables
Update `terraform.tfvars` with your actual values:

- **Resource Names**: App Service, Resource Group names
- **Managed Identity**: Client ID and Principal ID
- **Azure Services**: Cosmos DB, OpenAI, Search, Computer Vision endpoints

### Security Features
- ✅ User Managed Identity authentication
- ✅ No API keys in App Service settings
- ✅ Cosmos DB RBAC permissions
- ✅ Entra ID authentication for all services

## Commands

```bash
# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply configuration
terraform apply

# Destroy resources
terraform destroy
```

## Outputs

After deployment, Terraform will output:
- App Service URL
- Resource Group name  
- Managed Identity details