
from enrichment.utils.enums import Category
from enrichment.config.enrichment_config import enrichment_config

# Function to categorize images based on tags
def categorize_image(tags_with_confidence, confidence_score_value):
    categories_tags_values = enrichment_config.classifier_config_data
    categories = categories_tags_values["categories"]
    ignore_tags = set(tuple(tag) for tag in categories["ignore_tags"])

    # limiting tags considered based on confidence score
    tags = [tag.name.lower() for tag in tags_with_confidence if tag.confidence >= confidence_score_value]

    # when there is no text then ignore
    if not tags or not any(tag in tags for tag in ["text"]):
        return Category.IGNORE
    # tags that can be ignored
    elif any(all(tag in tags for tag in subset) for subset in ignore_tags):
        return Category.IGNORE
    # fallback for everything else
    else:
        return Category.GPT4_VISION