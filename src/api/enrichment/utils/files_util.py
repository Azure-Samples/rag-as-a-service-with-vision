
import json
import base64
from io import BytesIO
from PIL import Image

def json_file_load(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data

def get_image_format(base64_source: str):
    image_stream = BytesIO(base64.b64decode(base64_source))
    image = Image.open(image_stream)
    image_format = image.format
    return image_format