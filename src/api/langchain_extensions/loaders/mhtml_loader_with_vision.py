import base64
import email
import hashlib
import json
from pathlib import Path
import quopri
import re
from typing import Optional, Union
from langchain_core.documents import Document
import argparse
from loguru import logger as log
from bs4 import BeautifulSoup
from langchain_extensions.loaders.base_loader_with_vision import BaseVisionLoader
from enrichment.models.endpoint import MediaEnrichmentRequest
import urllib.parse

class MHTMLLoaderWithVision(BaseVisionLoader):

    supported_img_type = ["image/png", "image/jpeg", "image/jpg", "image/tiff", "image/bmp"]

    """Parse `MHTML` files with `BeautifulSoup`."""
    def __init__(
        self,
        file_path: Union[str, Path],
        separate_docs_for_images: bool = False,
        media_enrichment: Optional[dict[str, any]] = None,
        vision_workflow: Optional[dict[str, any]] = None,
        surrounding_text_start: Optional[int] = None,
        surrounding_text_end: Optional[int] = None,
        bs_kwargs: Union[dict, None] = None,
        open_encoding: Union[str, None] = None,
        get_text_separator: str = " "
    ):
        super(MHTMLLoaderWithVision, self).__init__(file_path, separate_docs_for_images, media_enrichment, vision_workflow, surrounding_text_start, surrounding_text_end)
        self.file_path = file_path
        self.open_encoding = open_encoding

        if bs_kwargs is None:
            bs_kwargs = {"features": "lxml"}
        self.bs_kwargs = bs_kwargs
        self.get_text_separator = get_text_separator


    def load_file(self) -> list[Document]:

        """
            Load MHTML file as Langchain document object based on the `media_enrichment` value.
            If `media_enrichment` is not None then image annotations and required metadata is added to the document.
            Else the default langchain MHTMLLoader behavior is supported for `page_content`.
        """
        try:

            message = None

            with open(self.file_path, "r", encoding=self.open_encoding) as f:
                message = email.message_from_string(f.read())
            
            documents = []
            
            if message:
                parts = message.get_payload()
                
                if not isinstance(parts, list):
                    parts = [message]

                # image_map contains all the images and their base encoded strings
                image_map = self.get_image_map(parts)
                
                # Generating langchain document object(s)
                for part in parts:                    
                    if part.get_content_type() == "text/html":

                        html_bytes = part.get_payload(decode=True)
                        html_decoded = html_bytes.decode()

                        soup = BeautifulSoup(html_decoded, **self.bs_kwargs)

                        content_location_value = None
                        
                        content_metadata: dict = {
                            "source": self.file_path,
                        }
                        
                        # custom metadata header parsing
                        # for now only X-Metadata or Snapshot-Content-Location will be included                       
                        try:
                            x_metadata_value, content_location_value = self.get_metadata_values(message)
                            
                            if content_location_value:
                                content_metadata['original_source'] = content_location_value
                            
                            if x_metadata_value:
                                x_metadata_dict = json.loads(x_metadata_value)

                                if x_metadata_dict and "id" in x_metadata_dict:
                                    doc_id = x_metadata_dict.pop("id")
                                    x_metadata_dict["doc_id"] = doc_id
                                content_metadata.update(x_metadata_dict)

                        except ValueError  as e:
                            log.warning(f"Error parsing X-Metadata or Snapshot-Content-Location as JSON for {self.file_path}: {e}")

                        # only if media enrichment is enabled the image annotations will be added 
                        # else it will behave like a default langchain mhtml loader
                        # for default implementation - from langchain_community.document_loaders import MHTMLLoader
                        if self.media_enrichment:
                            img_collection: dict = {}   

                            # Regular expression to match image file extensions
                            extensions = {mime.split('/')[-1] for mime in self.supported_img_type}

                            # Create the regex pattern
                            pattern = r'\.(' + '|'.join(extensions) + ')$'
                            image_extensions = re.compile(pattern, re.IGNORECASE)
                            
                            for tag in soup.find_all(["img", "a"]):
                                src = ""
                                try:
                                    if tag.name == 'a':
                                        if image_extensions.search(tag["href"]):
                                            # Check if the <a> tag contains an <img> tag, 
                                            # we dont want to process those 'a' tags as img tags processing will take care of it
                                            img_tag = tag.find('img')
                                            if img_tag:
                                                continue
                                            else:
                                                src = tag["href"]
                                        else:
                                            continue
                                    elif tag.name == 'img':
                                        src = tag["src"]
                                except Exception:
                                    log.warning(f"Image source/href {src} missing {self.file_path} in the image/a tag.")
                                    pass
                                
                                # there are few unique cases where anchor tags have the actual image url as `href`
                                # within the anchor tag an img tag is define with a different dimension size
                                # in such cases we want to just process the original image
                                # `sanitize_image_url` helps with resolving the scenario
                                src = self.sanitize_image_url(src, image_map)

                                src = self.get_abs_path(src, image_map)

                                if src not in image_map:              
                                    # Some MHTML files contain base64-encoded image data in the `src` attribute of `img` tags.
                                    # These images will not be part of already constructed image map.
                                    # The following code checks if the `src` attribute starts with "data:image/".
                                    # If it does, it assumes that the value is base64-encoded image data and adds it to the image map.
                                    if src.startswith("data:image/"):
                                        content_type, base64_data = src.split(";base64,", 1)
                                        _, file_extension = content_type.split("/",1)  
                                        
                                        image_data = base64.b64decode(base64_data)
                                        file_name = hashlib.md5(image_data).hexdigest()

                                        url = content_location_value + f"#unknown-{file_name}.{file_extension}"

                                        if not url in image_map:                                                        
                                            image_map[url] = base64_data
                                        src = url
                                    else:
                                        log.warning(f"Image source {src} not found for {self.file_path} in the image map.")
                                        continue               
                                
                                # logic to replace image tag with ![image descirption if any](image url)
                                img_annotation = f'![{src}]'

                                if not src in img_collection:
                                    img_collection[src] = image_map[src]

                                tag.replaceWith(soup.new_string(img_annotation))    
                            
                            if img_collection:
                                content_metadata["image_collection"] = img_collection
                        
                        text = soup.get_text(self.get_text_separator)
                        text = ' '.join([item for item in text.split(' ') if item != ''])         
                        
                        documents.append(Document(page_content=text, metadata=content_metadata))


            return documents
        
        except Exception as e:
            log.error(f"Error occured in MHTML loader, exception details - {e}")
            raise e

    def get_abs_path(self, url: str, image_map: dict[str,str]) -> str:

        if urllib.parse.urlparse(url).hostname is None:
            if url not in image_map:
                for key in image_map.keys():
                    if key.endswith(url):
                        return key
        
        return url
        
    def sanitize_image_url(self, url, image_map):
        # Define the regex pattern for dimensions in the image url (e.g., 150x150)
        pattern = r"-(\d+)x(\d+)"

        # Check if the dimensions are present in the URL
        if re.search(pattern, url):
            # Remove the dimensions
            cleaned_url = re.sub(pattern, "", url)
            if cleaned_url in image_map:
                return cleaned_url
    
        return url
        
    def get_metadata_values(self, message):
        x_metadata_value, content_location_value = None, None       
        if message['X-Metadata']:
            x_metadata_value = message['X-Metadata']
        if message['Snapshot-Content-Location']:
            content_location_value = message['Snapshot-Content-Location']

        return x_metadata_value, content_location_value

    def get_image_map(self, parts):
        """
        Get a mapping of image URLs to base64 encoded string from the MHTML parts.

        Args:
            parts (list[Message]): list of email message parts.

        Returns:
            dict[str, str]: A dictionary mapping image URLs to base64 encoded string.
        """
        image_map: dict[str, str] = {}
        for part in parts:
            content_type = part.get_content_type()
            if content_type in self.supported_img_type:
                location = part.get("content-location")
                if location in image_map:
                    continue
                
                img_b64 = part.get_payload().strip()
                image_map[location] = img_b64
        return image_map


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--file-path',
        dest='file_path',
        type=str,
        help='The name of the MHTML file to process'
    )
    parser.add_argument(
        '--separate_docs_for_images',
        dest='separate_docs_for_images',
        type=str2bool,
        help='Include images in individual document'
    )
    args = parser.parse_args()
    return args

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

if __name__ == "__main__":
    from enrichment.models.endpoint import Cache, Classifier, GPT4V, Features
    args = get_args()

    prompt = "You are an assistant whose job is to provide the explanation of images which is going to be used to retrieve the images."
    features = Features(cache=Cache(enabled=False), classifier=Classifier(enabled=True, threshold=0.8), gpt4v=GPT4V(enabled=True, prompt=prompt, llm_kwargs={"max_tokens": 800}))
    enrichment = MediaEnrichmentRequest(images=[], features=features)
    vision_workflow = {
    "enabled": True,
    "width_min_threshold": 200,
    "height_min_threshold": 100
    }

    loader = MHTMLLoaderWithVision(
        file_path=args.file_path,
        separate_docs_for_images=args.separate_docs_for_images,
        media_enrichment=enrichment,
        vision_workflow=vision_workflow,
        surrounding_text_end=100,
        surrounding_text_start=100
    )

    docs = loader.load()
    for index, doc in enumerate(docs):
        with open('loaders/doc-' + str(index) + ".html", 'w') as file:
            file.write(doc.page_content)
            file.write("\n Metadata below:\n")
            for key, value in doc.metadata.items():
                file.write(f"{key}: {value}\n")