import argparse
from loguru import logger as log
from typing import List, Any, Iterable
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# Keys to index into metadata dictionary
START_INDEX_KEY = 'start_index'
IMAGE_COLLECTION_KEY = 'image_collection'
POSITIONS_KEY = 'positions'
START_KEY = 'start'
END_KEY = 'end'
CONTENT_DOCUMENT_KEY = 'content_document'

# Constants for image annotation formatting
IMAGE_ANNOTATION_PREFIX = '!['
IMAGE_ANNOTATION_POSTFIX = '](%s)'

class RecursiveSplitterWithImage(RecursiveCharacterTextSplitter):

    def __init__(
        self,
        image_collection_in_metadata: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Creates a new RecursiveSplitterWithImage.
        """
        super().__init__(**kwargs)
        self._separators = ["\n\n", "\n", " "]  # Differs from the default - no "" in order to not truncate image URLs
        self._add_start_index = True  # Includes chunk `start_index` in metadata
        self.image_collection_in_metadata = image_collection_in_metadata 

    def split_documents(self, documents: Iterable[Document]) -> List[Document]:
        """
        Overrides the base split_documents implementation to preserve the proper 
        image annotation format across chunked documents. Updates chunk-level metadata 
        to remove `image_collection` field depending on the `image_collection_in_metadata` flag.
        Depends on the image annotation information encoded in the metadata by the MHTMLLoaderWithVision
        loader class.
        """
        # First, use the base RecursiveCharacterTextSplitter implementation to split the documents
        chunks = super().split_documents(documents)

        # Iterate over chunks and use metadata to see if image annotations have been broken up
        # If so, propagate image URLs / formatting appropriately
        for chunk in chunks:
            chunk_start = chunk.metadata[START_INDEX_KEY]
            chunk_end = chunk_start + len(chunk.page_content) - 1

            # If document doesn't contain images, it will not contain image_collection metadata
            # In this case, just use RecursiveCharacterTextSplitter chunks as-is and remove 
            # extraneous metadata if present
            if IMAGE_COLLECTION_KEY not in chunk.metadata:
                if CONTENT_DOCUMENT_KEY in chunk.metadata:
                    chunk.metadata.pop(CONTENT_DOCUMENT_KEY)
                chunk.metadata.pop(START_INDEX_KEY)
                continue

            # Compare chunk start/end with each image annotation start/end associated with that chunk
            # and augment chunks accordingly to preserve image annotation format
            # Note: early termination logic depends on images in image_collection being 
            # ordered by their position in the document.
            chunk_end_reached = False
            for image_url in chunk.metadata[IMAGE_COLLECTION_KEY].keys():
                image_annotation = chunk.metadata[IMAGE_COLLECTION_KEY][image_url]
                image_positions = image_annotation[POSITIONS_KEY]

                for position in image_positions:
                    image_annotation_start = position[START_KEY]
                    image_annotation_end = position[END_KEY]

                    # Case a: Image annotation starts in this chunk, but ends in a later one
                    if image_annotation_start >= chunk_start and image_annotation_start <= chunk_end and image_annotation_end > chunk_end:
                        log.debug('RecursiveSplitterWithImage case A: appending image URL to chunk')
                        chunk.page_content += IMAGE_ANNOTATION_POSTFIX % image_url
                        chunk_end_reached = True

                    # Case b: Image annotation ends in this chunk, but starts in an earlier one
                    elif image_annotation_end >= chunk_start and image_annotation_end <= chunk_end and image_annotation_start < chunk_start:
                        log.debug('RecursiveSplitterWithImage case B: prepending image annotation prefix to chunk')
                        chunk.page_content = IMAGE_ANNOTATION_PREFIX + chunk.page_content

                    # Case c: Chunk is a subset of the image annotation range - i.e. starts before and ends after this chunks
                    elif image_annotation_start < chunk_start and image_annotation_end > chunk_end:
                        log.debug('RecursiveSplitterWithImage case C: prepending image annotation prefix and appending image URL to chunk')
                        chunk.page_content = IMAGE_ANNOTATION_PREFIX + chunk.page_content + IMAGE_ANNOTATION_POSTFIX % image_url
                        chunk_end_reached = True

                    # Case d: If image annotation is already fully contained in this chunk, we don't need to do anything to the page_content
                    # Case e: If image annotation isn't in this chunk, we also don't need to do anything to page_content
                        
                    # If the image annotation starts after the chunk ends, we can stop searching in the current chunk
                    if image_annotation_start > chunk_end:
                        chunk_end_reached = True

                # Stop searching over images if we've reached the end of the chunk
                if chunk_end_reached is True:
                    break

            # Clean metadata depending on user flags
            # If we don't want to keep image collection metadata for a chunk (per flag or chunk is image-only)
            keep_description_in_metadata = self.image_collection_in_metadata and chunk.metadata[CONTENT_DOCUMENT_KEY]

            # clean and make it ready to persist to vector DB
            image_collection = self.get_image_collection(chunk, keep_description_in_metadata)
            
            # Stringify image collection metadata
            chunk.metadata[IMAGE_COLLECTION_KEY] = str(image_collection)

            # Remove other metadata only used for splitter logic that shouldn't be persisted to vector DB
            chunk.metadata.pop(CONTENT_DOCUMENT_KEY)
            chunk.metadata.pop(START_INDEX_KEY)

        return chunks
    
    def get_image_collection(self, chunk, keep_description_in_metadata):
        image_collection = {}
        chunk_start = chunk.metadata[START_INDEX_KEY]
        chunk_end = chunk_start + len(chunk.page_content) - 1

        for image_url in chunk.metadata[IMAGE_COLLECTION_KEY].keys():
            image_annotation = chunk.metadata[IMAGE_COLLECTION_KEY][image_url]
            image_positions = image_annotation[POSITIONS_KEY]

            # maintain image_collection to contain only the images resided in a chunk
            for position in image_positions:
                image_annotation_start = position[START_KEY]
                image_annotation_end = position[END_KEY]
                
                if image_annotation_start > chunk_end:
                    return image_collection

                if max(image_annotation_start, chunk_start) <= min(image_annotation_end, chunk_end):
                    image_collection[image_url] = chunk.metadata[IMAGE_COLLECTION_KEY][image_url].copy()
            
                    # Remove image 'positions' info from metadata - never persisted to vector DB regardless of metadata flag
                    image_collection[image_url].pop(POSITIONS_KEY)

                    if not keep_description_in_metadata:
                        image_collection[image_url].pop("description")
                    
                    # no need to go through all positions and should exit the loop
                    break

        return image_collection



def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mhtml_path', dest='mhtml_path', type=str, required=True)

    args = parser.parse_args()
    return args

if __name__ == "__main__":
    from loaders.mhtml_loader_with_vision import MHTMLLoaderWithVision
    from models.data.endpoint import MediaEnrichment, Features, Classifier, GPT4V, Cache

    # Add args parser
    args = _get_args()

    # Call the loader class here
    features = Features(cache=Cache(enabled=True, key_format="2024-04-17-{hash}", expiry=None), classifier=Classifier(enabled=False, threshold=0.0), gpt4v=GPT4V(enabled=True, prompt="You are an assistant whose job is to provide the explanation of images which is going to be used to retrieve the images.      Follow the below instructions: \n        - If the image contains any bubble tip then explain ONLY the bubble tip. \n        - If the image is an equipment diagram then explain all of the equipment and their connections in detail. \n        - If the image contains a table, try to extract the information in a structured way \n        - If the image device or product, try to describe that device with all the details related to shape and text on the device \n        - If the image contains screenshot, try to explain the highlighted steps. Ignore the exact text in the image if it is just an example for the steps and focus on the steps \n        - Otherwise, explain comprehensively the most important items with all the details on the image.", llm_kwargs={'temperature': 0, 'max_tokens': 2000, 'enhancements': {'ocr': {'enabled':True}, 'grounding':{'enabled':True}}}, detail_mode="auto"))
    enrichment = MediaEnrichment(domain="user_of5253", config_version="2024-04-17-fieldops-classifier-threshold-8", images=[], features=features)

    loader = MHTMLLoaderWithVision(
        file_path=args.mhtml_path,
        separate_docs_for_images=True,
        media_enrichment=enrichment
    )

    docs = loader.load()
    print(f'{len(docs)} MHTML documents loaded')
    print(docs[0].page_content) # Test
    print("\n")

    # Call the splitter class here
    splitter = RecursiveSplitterWithImage(chunk_size=1500, chunk_overlap=500, image_collection_in_metadata=True)
    print(f"MHTML Splitter initialized with chunk size {splitter._chunk_size} and overlap {splitter._chunk_overlap}")

    split_docs = splitter.split_documents(docs)
    for i, doc in enumerate(split_docs):
        print(f"Chunk {i} content:\n")
        print(doc.page_content)
        print("\n")