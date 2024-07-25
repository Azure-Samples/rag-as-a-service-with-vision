
# RAG Orchestrator API <!-- omit in toc -->

## Sections <!-- omit in toc -->

- [Overview](#overview)
- [Setup](#setup)
  - [Configure](#configure)
  - [Run Locally](#run-locally)
    - [Prerequisites](#prerequisites)
    - [Create virtual environment](#create-virtual-environment)
    - [Create ENV file](#create-env-file)
    - [Install Dependencies](#install-dependencies)
    - [Run the API](#run-the-api)
    - [Visit the Swagger definition](#visit-the-swagger-definition)

## Overview

This RAG API facilitates the ingestion of data into a vector store and the retrieval of the content from the vector store to be used in a RAG-based flow.

The API also allows domains to manage their configuration.

## Setup

### Configure

The following configuration parameters need to be defined:

- **OPENAI_API_VERSION** [REQUIRED]: The OpenAI API version.
- **AZURE_OPENAI_API_KEY** [REQUIRED]: The OpenAI API key.
- **AZURE_MLLM_DEPLOYMENT_MODEL** [REQUIRED]: The OpenAI multi-modal LLM model (i.e. GPT-4v, GPT 4o)

- **AZURE_SEARCH_ENDPOINT** [REQUIRED]: The Azure AI Search endpoint.
- **AZURE_SEARCH_API_KEY** [REQUIRED]: The Azure AI Search key.

- **AZURE_COSMOS_DB_URI** [REQUIRED]: The CosmosDb connection string.
- **AZURE_COSMOS_DB_KEY** [REQUIRED]: The CosmosDb key.
- **AZURE_COSMOS_DB_DATABASE** [REQUIRED]: The CosmosDb database name.
- **AZURE_COSMOS_DB_CONTAINER** [REQUIRED]: The CosmosDb container name.

- **AZURE_COMPUTER_VISION_ENDPOINT** [REQUIRED]: The Azure computer vision endpoint.
- **AZURE_COMPUTER_VISION_KEY** [REQUIRED]: The Azure computer vision key.

### Run Locally

#### Prerequisites

- [Python 3.11](https://www.python.org/downloads/release/python-3110/)
- [Docker](https://www.docker.com/) (Optional)

#### Create virtual environment

If running outside of the `dev-container`, create your virtual environment.

```bash
# Under ./src/api/ directory
python -m venv venv
source ./venv/Scripts/activate
```

#### Create ENV file

Copy the [sample.env](./configs/sample.env) to .env and define the parameters based on the [configure](#configure) section.

```bash
cp ./configs/sample.env ./configs/.env
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Run the API

This can be done via command line:

```bash
python -m main
```

Or via the VS Code debugger using the provided launch task "Python Debugger: API".

![VS Code API launch task](/docs/assets/vscode-launch-api.png)

#### Visit the Swagger definition

Once the app starts, visit `localhost:{PORT}/docs` to view the autogenerated Swagger definition for the API. You can make requests using the Swagger UI, or via Postman. 

![Swagger UI API](/docs/assets/swagger-ui-api.png)