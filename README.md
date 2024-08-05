# RAG with Vision Application Framework

## Features

This repository provides an application framework for a Python-based [retrieval-augmented generation (RAG)](https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview) pipeline that can utilize both textual and image content from MHTML documents to answer user queries, leveraging Azure AI Services, Azure AI Search, and Azure OpenAI Service.
It also provides an interface for users to manage RAG pipeline configurations, as well as starter code to run and evaluate the end-to-end inference flow against a sample dataset, which enables further experimentation to fine-tune the pipeline to best meet user needs for a given dataset.

## Getting Started

### Prerequisites and running the API

To see more information on the prerequisites and how to run the RAG with Vision API locally, see the [`api` folder README](src/api/README.md).

This repository also includes a [devcontainer](.devcontainer/devcontainer.json) that can be used in VSCode with the `ms-vscode-remote.remote-containers` extension.

### Understanding the architecture

The overall inference flow can be described via the following diagram:

![Inference flow](docs/assets/inference-flow.drawio.png)

For a full overview of the RAG with Vision architecture, including the document ingestion process and the image enrichment service, see [this architecture document](docs/vision-rag-architecture.md).
An introduction to RAG pipeline evaluation and the starter evaluation flows provided in this repo, along with suggestions for collecting inner- and outer-loop feedback, can be found [here](docs/evaluation.md).
