## RAG with Vision Application Framework Changelog

<a name="x.y.z"></a>
# 1.0.0 (2024-08-14)

*Features*

*Ingestion flow*: Ingests MHTML files into Azure AI Search using a newly developed enrichment pipeline.

*Enrichment flow*: Enhances ingested documents by classifying images based on their content, using a multi-modal LLM (MLLM) to generate image descriptions, and caching enrichment results to speed up the process.

*RAG with vision pipeline* : Utilizes enrichment data to search for images and incorporates the enrichment pipeline during inference.

*Evaluation starter code*: Assesses the performance of a particular RAG pipeline configuration using various metrics, including ROUGE recall and LLM-as-a-judge techniques.
