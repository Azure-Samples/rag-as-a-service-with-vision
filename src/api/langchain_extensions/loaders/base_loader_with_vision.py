import base64
import os
import asyncio
import copy
from http.client import INTERNAL_SERVER_ERROR, TOO_MANY_REQUESTS
from typing import Optional
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.documents import Document
from loguru import logger as log
import platform
import urllib.parse
import unicodedata
import re
from PIL import Image
from io import BytesIO

from enrichment.enrichment_service import EnrichmentService
from models.data.endpoint import MediaEnrichment
from timeit import default_timer as timer

class BaseVisionLoader(BaseLoader):

    def __init__(
        self,
        file_path: str,
        separate_docs_for_images: bool,
        media_enrichment: dict[str, any] = None,
        vision_workflow: dict[str, any] = None,
        surrounding_text_start: Optional[int] = None,
        surrounding_text_end: Optional[int] = None
    ):
        self.media_enrichment = None

        if media_enrichment:
            media_enrichment_req = dict(media_enrichment)
            media_enrichment_req["images"] = []
            self.media_enrichment = MediaEnrichment(**media_enrichment_req)

        self.destination_image_folder = os.path.dirname(
            file_path).replace("pending", "images")
        self.image_path_prefix =  os.path.basename(file_path).replace(".","-").lower()
        self.separate_docs_for_images = separate_docs_for_images
        self.enrichment_service = EnrichmentService()
        self.MAX_BATCH_SIZE = int(os.environ.get("LOADER_BATCH_MAX_SIZE", 1))
        self.MIN_BATCH_SIZE = int(os.environ.get("LOADER_BATCH_MIN_SIZE", 1))
        self.LOADER_BATCH_COUNTER = int(os.environ.get("LOADER_BATCH_COUNTER", 10))
        self.surrounding_text_start = surrounding_text_start
        self.surrounding_text_end = surrounding_text_end
 
        self.vision_workflow = vision_workflow
    
    def _sanitize_filename(self, filename: str) -> str:

        os_name = platform.system()
        filename = urllib.parse.unquote(filename)
        if os_name != "Windows":
            filename = unicodedata.normalize('NFKC', filename)
        else:
            # This is mainly for window machines used by developers
            filename = unicodedata.normalize('NFKD', filename).encode('ascii', 'ignore').decode('ascii')

        filename = re.sub(r'[^\w\s.-]', '', filename.lower())
        return filename

    def _convert_url_to_filename(self, image_url) -> str:
        image_url = image_url.replace("#unknown-", "/")
        path = urllib.parse.urlparse(image_url).path
        filename = os.path.basename(path)
        sanitized_filename = self._sanitize_filename(filename)
        return sanitized_filename
    
    def get_image_path(self, image_url) -> str:
        image_name = self._convert_url_to_filename(image_url)

        image_file_path = os.path.join(
            self.destination_image_folder, f"{self.image_path_prefix.lower()}_{image_name}")
        
        return image_file_path

    def load_file(self) -> list[Document]:
        pass
    
    def load(self) -> list[Document]:
        """
           If media enrichment is enabled then image annotations will be processed           
                When `separate_docs_for_images` is set to False, it loads only a single document.
                Alternatively, when `separate_docs_for_images` is True, it loads as multiple documents:
                - One document for the main content
                - Additional documents for each associated image that has description generated via enrichment service call
                The document metadata includes information from the `X-Metadata` and `Snapshot-Content-Location` header.
                The image collection metadata will have:
                - Image URL
                - Image description
                - Start and end indexes array of the image annotation
            Else nothing will be done and the langchain documents will be returned as is
        """
        try:
                docs = self.load_file()

                # If media enrichment is enabled then image annotations will be prcessed 
                # else nothing will be done and the documents will be returned as is
                total_start_time = timer()

                documents = []
                images_count = 0 
                for doc in docs:
                    metadata = doc.metadata
                    content = doc.page_content
                    
                    # If the document has images in it, it will have image_collection present in its metadata
                    if "image_collection" in metadata:
                        if self.vision_workflow:
                            image_collection, content = self.remove_invalid_images(metadata["image_collection"], content)  
                        else:
                            image_collection = metadata["image_collection"]

                        images_count = len(image_collection)
                        metadata.pop("image_collection")
                        
                        image_collection_new = {}
                        image_annotation_list = []                  

                        # image_map contains all the images and their descirption if image is processed by GPT4V
                        start_time = timer()
                        batch_size = self.determine_batch_size(len(image_collection))
                        
                        image_map = asyncio.run(self.async_get_image_description_map(image_collection, self.media_enrichment, batch_size, content))
                        
                        end_time = timer()
                        elapsed_time = end_time - start_time

                        if image_map:                    
                            log.debug(f"Image description generation took {elapsed_time:.4f} seconds for {len(image_map)} images.")
                        
                            for url in image_collection:
                                image_marker = f"![{url}]"
                                image_path = self.save_image(url, image_collection[url])
                                image_annotation = f"({url})"
                                desc = image_map[url]
                                
                                # only generate image docs if there is a description associated with image and the flag is enabled                           
                                if self.separate_docs_for_images and desc:
                                    img_doc_str = f"![{desc}]({url})"
                                    doc_exists = any(existing_doc.page_content == img_doc_str for existing_doc in documents)
                                    # check if image doc was already added before
                                    if not doc_exists:                            
                                        img_doc_metadata = metadata.copy()
                                        img_doc_collection = {
                                            url: {
                                                "description": desc,
                                                "image_path": image_path,
                                                "positions": [{"start": 0, "end": len(img_doc_str) - 1}]
                                            }
                                        }
                                        img_doc_metadata["image_collection"] = img_doc_collection
                                        img_doc_metadata["content_document"] = False
                                        documents.append(Document(page_content=img_doc_str, metadata=img_doc_metadata))
                                # add description to content doc only if separate image docs are not created
                                elif not self.separate_docs_for_images:                                
                                    image_annotation = f'![{desc}]' + image_annotation

                                # Replace all image markers with the full image annotation for each instance of the image in the doc
                                # Initialize the new image collection dictionary with an entry for each image_url, but no positions info yet
                                # Save image annotation to list
                                content = content.replace(image_marker, image_annotation) # Replaces all instances of image_marker with image_annotation
                                image_collection_new[url] = {"description": desc, 'positions': [], 'image_path': image_path}
                                image_annotation_list.append((url, image_annotation))
                            
                            # Tterate over all image annotations now that content is finalized and calculate positions
                            if content:
                                for (img_url, annotation) in image_annotation_list:
                                    content, image_collection_new = self.update_metadata_with_image_annotation_positions(content, annotation, image_collection_new, img_url)

                            metadata["image_collection"] = image_collection_new
                            metadata["content_document"] = True
                        
                        if content:
                            documents.append(Document(page_content=content, metadata=metadata))
                    
                    # If no images in the document, just append the document as-is
                    else:
                        documents.append(doc)        

                    total_end_time = timer()
                    elapsed_time = total_end_time - total_start_time
                    log.debug(f"MHTML Vision load took {elapsed_time:.4f} seconds for {images_count} images.")
                return documents
        except Exception as e:
            log.error(f"MHTMLLoader exception occurred, exception details - {e}", exc_info=True)

    def get_surrounding_text(self, keyword, text):
        # Find all occurrences of the keyword in the text
        image_pattern = r'!\[[^\]]*\]'
        # Regular expression pattern to match (url) ending with image extensions
        url_pattern = r'\([^\s\)]+\.(png|jpeg|jpg|gif|bmp|webp)\)'

        def replace_image(match):
            # Check if the match contains the exception_url
            if keyword in match.group(0):
                return match.group(0)
            return ''

        # Remove all markdown images except the one containing exception_url
        text = re.sub(image_pattern, replace_image, text)
        # Remove URLs ending with image extensions
        text = re.sub(url_pattern, replace_image, text)

        matches = re.finditer(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE)
        
        # Initialize the result list
        result = []
        
        # Iterate over each match
        for match in matches:
            # Get the start and end indices of the match
            start, end = match.span()
            
            # Calculate the surrounding text indices
            before_start = max(0, start - self.surrounding_text_start)
            after_end = min(len(text), end + self.surrounding_text_end)
            
            # Ensure that the surrounding text does not have broken words
            while before_start > 0 and text[before_start:start] and not text[before_start:start][0].isspace():
                before_start -= 1

            if text[before_start:end]:
                result.append("Previous text:\n"+text[before_start:end].strip())
            
            while after_end < len(text) - 1 and text[end:after_end] and not text[end:after_end][-1].isspace():
                after_end += 1

            if text[end+1:after_end]:
                result.append("Next text:\n"+text[end+1:after_end].strip())

        return result
    
    def update_metadata_with_image_annotation_positions(self, content, image_annotation, image_collection, url):    
        img_tag_end_index = 0  # Initialize the img tag end index
        while True:
            annotation_start_index = content.find(image_annotation, img_tag_end_index)
            if annotation_start_index == -1:
                break  # No more image markers found, exit the loop

            # Calculate the annotation end index
            annotation_end_index = annotation_start_index + len(image_annotation) - 1

            # Update the img tag end index for the next iteration
            img_tag_end_index = annotation_end_index

            # Update image_collection
            if url in image_collection:
                image_collection[url]['positions'].append({'start': annotation_start_index, 'end': annotation_end_index})
            else:
                log.error('Not supposed to reach this error - image_collection should be populated with ')
            
            log.debug(f"src-{url}, start-{annotation_start_index}, end-{annotation_end_index}, img-end-{img_tag_end_index}")         

        return content, image_collection        

    async def async_get_image_description_map(self, image_collection, media_enrichment, batch_size, content):
        """
        Get a mapping of image URLs to their descriptions from the MHTML parts.

        Args:
            parts (list[Message]): list of email message parts.
            media_enrichment (MediaEnrichment): The media enrichment configuration.

        Returns:
            dict[str, str]: A dictionary mapping image URLs to descriptions.
        """
        tasks = []
        results: dict[str, str] = {}
        responses = []

        if __debug__:
            batch_loop_count = 0
        
        try: 
            for url in image_collection:
                img_b64 = image_collection[url]                
                # this is needed for concurrent calls
                media_enrichment_copy =  copy.deepcopy(media_enrichment)
                surrounding_text = ''
                if self.surrounding_text_start and self.surrounding_text_end:
                    surrounding_text = self.get_surrounding_text(url, content)
                # Store URL along with its corresponding task
                tasks.append((url, self.async_get_image_description(img_b64, media_enrichment_copy, surrounding_text)))
                
                if len(tasks) >= batch_size: # Limit to batch_size concurrent tasks
                    responses = await asyncio.gather(*[task for _, task in tasks])
                    
                    for url, response in zip([url for url, _ in tasks], responses):
                        results[url] = response

                    if __debug__:
                        total_count = len(image_collection)
                        batch_loop_count = batch_loop_count + 1
                        log.debug(f"Finished executing concurrent task {batch_loop_count} of {round(total_count/batch_size)}")
                    tasks.clear()

            # Gather any remaining tasks
            if tasks:
                responses = await asyncio.gather(*[task for _, task in tasks])
                for url, response in zip([url for url, _ in tasks], responses):
                    results[url] = response

                if __debug__:
                    total_count = len(image_collection)
                    batch_loop_count = batch_loop_count + 1
                    log.debug(f"Finished executing concurrent task {batch_loop_count} calls of {round(total_count/batch_size)}")

            return results
        except Exception as e:
            all_running_tasks = asyncio.all_tasks()
            for task in all_running_tasks:
                task.cancel()
                 # Wait for the tasks to truly cancel
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            custom_message = 'Tasks cancelled because of an exception: ' + str(e)
            raise Exception(custom_message) from e

    async def async_get_image_description(self, img_b64, media_enrichment, surrounding_text):
        """
        Get a description for the given image using media enrichment.

        Args:
            img (str): The base 64 encode image string.
            media_enrichment (MediaEnrichment): The media enrichment configuration.

        Returns:
            str: The description generated for the image.
        """  
        try:        
            media_enrichment.images = [img_b64]
            media_enrichment.surrounding_text = surrounding_text
            resp = await self.enrichment_service.async_get_media_enrichment_result(media_enrichment)
            generated_response = resp.generated_response
            desc = generated_response.content if generated_response else ""            
            return desc
        except asyncio.CancelledError:
            log.error(f"MHTMLLoader exception occurred as one of the other request is cancelled") 
        except Exception as e:
            log.error(f"MHTMLLoader exception occurred when calling enrichment services, exception details - {e}", exc_info=True)
            # system failures and rate limiting exceptions will cancel out the other requests
            if hasattr(e, 'status_code') and (e.status_code >= INTERNAL_SERVER_ERROR or e.status_code == TOO_MANY_REQUESTS) :
                raise e # Re-raise the exception after logging     


    def save_image(self, url: str, image_base64: str) -> str:
        os.makedirs(self.destination_image_folder, exist_ok=True)
        
        image_path = self.get_image_path(url)
        image_bytes = base64.b64decode(image_base64)

        with open(image_path, 'wb') as file:
            file.write(image_bytes)
    
        return image_path 

    def determine_batch_size(self, image_count):
        """
        Determine batch size based on the number of images.

        Args:
        - image_count (int): The total number of images to be processed.

        Returns:
        - batch_size (int): The determined batch size.
        """

        log.debug(f"Determining batch size for {image_count} images")

        # Set initial batch size
        batch_size = 1

        # If image count is greater than 5, adjust batch size
        if image_count >= 5:
            batch_size = min(((image_count // self.LOADER_BATCH_COUNTER) + 1) * 2, self.MAX_BATCH_SIZE)

        log.debug(f"Determined batch size for the mhtml loader is {batch_size}")

        return batch_size

    
    def remove_invalid_images(self, img_collection, content):        
        min_width = self.vision_workflow.get("width_min_threshold", 0)
        min_height = self.vision_workflow.get("height_min_threshold", 0)
        log.debug(f'Required image dimensions, width - {min_width} height - {min_height}')
        
        # image dimensions check
        for k in list(img_collection.keys()):
            width, height = self.calculate_image_size(img_collection[k])
            if width < min_width or height < min_height:
                log.debug(f'Image doesnt follow the required dimensions, width is {width} and height is {height}. Img url is - {k}')
                img_annotation = f'![{k}]'
                content = content.replace(img_annotation, "")            
                del img_collection[k]  

        return img_collection, content    
    
    def calculate_image_size(self, encoded_string):
        # Decode the base64 encoded string
        image_data = base64.b64decode(encoded_string)
        
        # Open the image using PIL
        img = Image.open(BytesIO(image_data))
        
        # Get the size of the image
        width, height = img.size
        
        return width, height