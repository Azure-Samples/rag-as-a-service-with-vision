from fastapi.exceptions import HTTPException
from fastapi import status

class CustomServiceException(HTTPException):
    def __init__(self, detail, service_name, status_code):
        self.detail = f"Exception occurred in '{service_name}', exception details - {detail}"
        self.status_code = status_code

class BadRequestError(HTTPException):
    '''Raise when there is bad data in the request'''
    def __init__(self, detail):
        self.detail = detail
        self.status_code = status.HTTP_400_BAD_REQUEST

