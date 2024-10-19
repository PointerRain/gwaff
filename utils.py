from urllib.parse import urlencode
import requests
from io import BytesIO
import json
import discord

from database import DatabaseReader

MAX_RETRIES = 5


def retry_request(request_func, url, **kwargs):
    '''
    Handles retry logic for making requests.

    Parameters:
        request_func: Function to call for the request (e.g., requests.get).
        url: The URL to request.
        kwargs: Additional arguments for the request.

    Returns: The result of the request_func, or None on failure.
    '''
    count = 0
    while count < MAX_RETRIES:
        try:
            response = request_func(url, **kwargs)
            response.raise_for_status()  # Raises an HTTPError for bad responses
            return response
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {count+1} failed: {str(e)}")
            count += 1
            if count < MAX_RETRIES:
                time.sleep(1 << count)
            else:
                logger.error("Max retries reached, skipping.")
                return None


def request_api(url: str, **kwargs) -> dict:
    '''
    Requests JSON data from the given API.

    Returns: dict of the requested data.
    '''
    if kwargs:
        url = url_constructor(url, **kwargs)

    # Timeout to avoid hanging
    response = retry_request(requests.get, url, timeout=10)
    if response:
        try:
            return response.json()  # Parse JSON response
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            return None
    return None


def request_img(url: str, **kwargs):
    '''
    Requests an image from the given URL.

    Returns: a file-like object of the image that matplotlib can read.
    '''
    if kwargs:
        url = url_constructor(url, **kwargs)
    
    headers = kwargs.get('headers', {"User-Agent": "Mozilla/5.0"})
    
    response = retry_request(requests.get, url, headers=headers, timeout=10, stream=True)
    if response:
        return BytesIO(response.content)  # Return image as a file-like object
    return None


def url_constructor(base: str, **kwargs: dict) -> str:
    '''
    Constructs a url from a base url and several key-values.

    Returns: str of the final url.
    '''
    query = urlencode(kwargs)
    return f"{base}?{query}"


def resolve_member(interaction: discord.Interaction,
                   user: discord.User) -> discord.User:
    '''
    Chooses the member between a specified member, and the triggering member.
    '''
    dbr = DatabaseReader()
    if user is not None:
        if dbr.get_profile_data(user.id):
            return user
    if interaction is not None:
        if dbr.get_profile_data(interaction.user.id):
            return interaction.user
    return False


def ordinal(n: int) -> str:
    suffixes = {1: "st", 2: "nd", 3: "rd"}
    i = n if (n < 20) else (n % 10)
    suffix = suffixes.get(i, 'th')
    return str(n) + suffix
