from pydantic import BaseModel


class TempFileReference(BaseModel):
    file_name: str
    temp_file_path: str
