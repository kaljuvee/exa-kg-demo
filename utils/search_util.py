# Description: This utility file will contain the core functions for interacting with the Exa.ai API.

import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Constants ---
EXA_API_KEY = os.environ.get("EXA_API_KEY", "ba4e615f-b7e9-4b91-b83f-591aa0ec5132")
EXA_API_BASE_URL = "https://api.exa.ai"

# --- API Functions ---

def search(query: str, num_results: int = 10, include_domains: list = None, exclude_domains: list = None):
    """ 
    Performs a search using the Exa API.

    Args:
        query: The search query.
        num_results: The number of results to return.
        include_domains: A list of domains to include in the search.
        exclude_domains: A list of domains to exclude from the search.

    Returns:
        A dictionary containing the search results.
    """
    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "numResults": num_results,
        "includeDomains": include_domains,
        "excludeDomains": exclude_domains,
    }
    try:
        response = requests.post(f"{EXA_API_BASE_URL}/search", headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def find_similar(url: str, num_results: int = 10):
    """
    Finds similar links to a given URL using the Exa API.

    Args:
        url: The URL to find similar links for.
        num_results: The number of similar links to return.

    Returns:
        A dictionary containing the similar links.
    """
    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "url": url,
        "numResults": num_results,
    }
    try:
        response = requests.post(f"{EXA_API_BASE_URL}/findSimilar", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_contents(ids: list):
    """
    Retrieves the contents of a list of Exa result IDs.

    Args:
        ids: A list of Exa result IDs.

    Returns:
        A dictionary containing the contents of the results.
    """
    headers = {
        "x-api-key": EXA_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "ids": ids,
    }
    try:
        response = requests.post(f"{EXA_API_BASE_URL}/contents", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

