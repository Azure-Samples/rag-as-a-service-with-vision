# Enrichment at Ingestion Features <!-- omit in toc -->

## Sections <!-- omit in toc -->

## Overview

Enrichment at Ingestion (or EnrichmenService) is a service integrated with Azure AI Services, including Vision and OpenAI Services.

In this document, we will cover three features: Multi-modal LLM, Classifier and Cache.

## RAG Config Sample

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
            },
        }
    },
```

## MLLM



## Classifier

### Why?

The classifier can help reducing the number of calls made to GPT Vision, thereby decreasing latency and costs.

The classifier analyzes images using Azure Vision Tags to categorize them based on their content. It follows a set of rules to determine the appropriate action for each image:
 
**Ignore Category**:
 
- If the image does not contain any tags, it is categorized as "IGNORE".
- Images without text or those that are logos are also categorized as "IGNORE". These images are considered irrelevant for further processing.
 
**GPT Vision Category**:
 
- If the image contains text and keywords related to diagrams, designs, software, or websites, it is categorized as "GPT_VISION". These images are suitable for further processing with GPT Vision to extract additional information.

### Usage

The cache uses Azure Computer Vision to determine the tags of the image.

The classifier requires a `threshold`, which represents the confidence score we want to consider for the provided tags. By setting a specific threshold, we filter out tags with confidence scores below that level, ensuring that only reliable predictions are retained. The value ranges between 0 and 1.

```json
    "classifier": {
        "enabled": true,
        "threshold": 0.8
    },
```


## Cache

### Why?

Enrichment is a very cost-full operation and it is important to avoid redundant calls to the Enrichment Service.

In terms of token usage, GPT Vision has three modes for its detail level: `low`, `high`, and `auto` (default). The cost of the service is different for each mode. For `low` mode, the cost of the service is 85 tokens per image regardless what is the image resolution. For the `high` resolution mode, it depends on the size of image. For example, if the image size is 4096 x 8192, the cost will be 1105 tokens. In this mode, GPT uses a hierarchical bird approach to adjust the image resolution and tile it for a better detailed output. The images with resolution higher than 512 x 512 are considered high resolution images.
 
 In terms of latency, it depends on the size and resolution of images and the number of services that are being called, the latency of the service can be high from 6s to 1 min. For example, the latency of the service for a 4096 x 8192 image can be up to one minute. It means ingestion of a document with 10 images can take up to 10 minutes without parallelization.

 To avoid redundant calls in the Enrichment Service to underlying services including GPT and image analysis services, a cache can be used to store the results of the enrichment service to reduce the cost (almost zero if the result is cached for all consequent enrichment calls and Azure Cosmos DB used as a cache) and latency of the service.

 ### Usage

The cache uses Azure Cosmos Db for caching the results of the Enrichment Service.

The cache will be a key/value store with an expiry date that will be refreshed anytime that the key is accessed. The key will be generated from the input of the enrichment service and the value will be the result of the enrichment service. The expiry date will be set based on the configuration of the enrichment service. For example, the request will be with an additional field named `expiry` in the time span format as below:

```json
    "cache": {
        "enabled": true,
        "expiry": "DD:HH:MM:SS",
        "key_format": "{hash}",
    },
```

- **Key**: It will be generated from the input of the Enrichment Service using SHA-256 algorithm in the format `{domain}-{version}-{hash of the images and features}`. This format ensures that any change in the content of the image or the settings in `features`, including prompt and enhancement flags, will generate a new key/value. The old key/value will be expired based on the expiry date.
 
- **Value**: It will be the result of the Enrichment Service, including the vision and OpenAI services.
 
- **Eviction Policy**: It will be set based on the expiry date of the key/value. The expiry date will be refreshed anytime the key is accessed. In Azure Cosmos DB, the expiry date needs to be updated manually in the application code using the TTL feature of Azure Cosmos DB or by using a custom field for the `expiry` and an `index` on this field in the document.