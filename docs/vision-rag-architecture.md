# Architecture: Vision RAG

## Problem statement

The [Retrieval-Augmented Generation architecture](https://learn.microsoft.com/en-us/azure/search/retrieval-augmented-generation-overview) has become more common with the advent of more mature generative AI models, giving users a way to ground LLM responses in data retrieved from some document store, typically a vector database.
The classic version of the pattern assumes text-only content in the document store;
however, in many enterprise scenarios, the content that users wish to query can contain images and tables that are also essential to accurately answering their questions.

To address this use case, it makes sense to incorporate a **multimodal LLM**, such as [GPT-4V](https://techcommunity.microsoft.com/t5/ai-azure-ai-services-blog/gpt-4-turbo-with-vision-on-azure-openai-service/ba-p/3979933) or [GPT-4o](https://azure.microsoft.com/en-us/blog/introducing-gpt-4o-openais-new-flagship-multimodal-model-now-in-preview-on-azure/), into our RAG workflow.

- Talk about options for how to incorporate multimodal LLM and the approach we chose

### Considerations

- Cost and latency
  - At the time of development, GPT-4V was the only multimodal LLM available via Azure OpenAI, and latency/cost were high enough based on expected load on the system that we felt it would be better to explore the pattern of generating and querying text descriptions of images as opposed to direct inference against a multimodal LLM.
  However, as the technology develops and newer models are released with
  - not all images in documents are relevant or contain useful information (e.g. business logo letterhead, etc.) - we propose using a classifier to identify images for which using the enrichment service to generate an image description would have most value
- mHTML document format - for our use case, the document store we were considering was primarily HTML documents. HTML static content doesn't preserve the image data in the document, so we chose to convert the documents to mHTML format to ensure all required content was captured from the documents.

## System architecture

### Enrichment workflow

Enrichment is a service integrated with Azure AI Services, including Computer Vision and OpenAI Services. It has three main features: Multimodal LLM, Classifier and Caching.

![Enrichment service workflow](./assets/enrichment-flow.drawio.png)

### RAG Config Sample

RAG config sample that uses all the enrichment features:

```json
    "media_enrichment": {
        "features": {
            "mllm": {
                "enabled": true,
                "prompt": "Be a helpful assistant and answer anything!",
                "llm_kwargs": {},
                "model": "gpt-4o",
                "detail_mode": "auto"
            },
            "classifier": {
                "enabled": true,
                "threshold": 0.8
            },
            "cache": {
                "enabled": true,
                "expiry": null,
                "key_format": "2024-07-22-{hash}"
            }
        }
    }
```

#### Multimodal LLM

The multimodal LLM is a model with vision features to understand the content of images. Examples of models are GPT-4v or GPT-4o, which need to be specified in the `model` field.

The MLLM also requires a `prompt`, which is specific for image summarization and different from the one used at inferencing time.

You can complement other LLM arguments by using `llm_kwargs`, such as temperature or max tokens.


#### Classifier

The classifier helps reducing the number of calls made to GPT Vision, thereby decreasing latency and costs.

The classifier analyzes images using Azure Computer Vision Tags to categorize them based on their content. It follows a set of rules to determine the appropriate action for each image:
 
- Ignore Category: If the image does not contain any tags, or if it is an image without text or a logo, it is categorized as "IGNORE". These images are considered irrelevant for further processing.
 
- GPT Vision Category: If the image contains text and keywords related to diagrams, designs, software, or websites, it is categorized as "GPT VISION". These images are suitable for further processing with GPT Vision to extract additional information.

The classifier requires a `threshold`, which represents the confidence score we want to consider for the provided tags. By setting a specific threshold, we filter out tags with confidence scores below that level, ensuring that only reliable predictions are retained. The value ranges between 0 and 1.


#### Caching

Enrichment is a cost-full operation and it is important to avoid redundant calls to the Enrichment Service.

GPT Vision has three modes for its detail level: `low`, `high`, and `auto` (default). The cost of the service is different for each mode. For `low` mode, the cost of the service is 85 tokens per image regardless what is the image resolution. For the `high` resolution mode, it depends on the size of image. For example, if the image size is 4096 x 8192, the cost will be 1105 tokens. In this mode, GPT uses a hierarchical bird approach to adjust the image resolution and tile it for a better detailed output. The images with resolution higher than 512 x 512 are considered high resolution images.
 
In terms of latency, it depends on the size and resolution of images and the number of services that are being called, the latency of the service can be high from 6s to 1 min. For example, the latency of the service for a 4096 x 8192 image can be up to one minute. It means ingestion of a document with 10 images can take up to 10 minutes without parallelization.

To avoid redundant calls in the Enrichment Service to underlying services including GPT and image analysis services, a cache can be used to store the results of the enrichment service to reduce the cost (almost zero if the result is cached for all consequent enrichment calls and Azure Cosmos DB used as a cache) and latency of the service.

The cache uses Azure Cosmos Db for caching the results of the Enrichment Service.

The cache will be a key/value store with an expiry date that will be refreshed anytime that the key is accessed. The key will be generated from the input of the enrichment service and the value will be the result of the enrichment service. The expiry date will be set based on the configuration of the enrichment service. For example, the request will be with an additional field named `expiry` in the time span format as below:

```json
    "cache": {
        "enabled": true,
        "expiry": "DD:HH:MM:SS",
        "key_format": "{hash}",
    },
```

- Key: It will be generated from the input of the Enrichment Service using SHA-256 algorithm in the format `{domain}-{version}-{hash of the images and features}`. This format ensures that any change in the content of the image or the settings in `features`, including prompt and enhancement flags, will generate a new key/value. The old key/value will be expired based on the expiry date.
 
- Value: It will be the result of the Enrichment Service, including the Computer Vision and OpenAI services.
 
- Eviction Policy: It will be set based on the expiry date of the key/value. The expiry date will be refreshed anytime the key is accessed. In Azure Cosmos DB, the expiry date needs to be updated manually in the application code using the TTL feature of Azure Cosmos DB or by using a custom field for the `expiry` and an `index` on this field in the document.


### Document ingestion workflow

#### Document loader

TODO: Include context from MHTMLLoaderWithVision design doc

- Discuss base class for vision loader vs MHTML-specific loader
  - metadata parsing?

#### Document splitter

TODO: Include context from RecursiveSplitterWithImage design doc

### Inference workflow

TODO: insert full system diagram for inference flow based on user query (query -> search -> formulate context -> chat)

### Maybe - API endpoints?
