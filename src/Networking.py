import requests
from typing import Dict


def https_post(url: str, parameters: Dict = None, files: Dict = None) -> requests.Response:
    """
    Raw https post with optional parameters
    :param url: POST URL
    :param parameters: Parameters
    :param files: Multipart file data to send
    :return: None
    """
    return requests.post(url, parameters, files=files)


def https_get(url: str, parameters: Dict = None) -> requests.Response:
    """
    Raw https get with optional parameters
    :param url: GET URL
    :param parameters: Parameters
    :return: Requests GET object with return code and payload
    """
    return requests.get(url, parameters)