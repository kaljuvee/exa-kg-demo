import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import requests

# Add parent directory to path to import utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.search_util import search, find_similar, get_contents

class TestSearchUtil(unittest.TestCase):

    @patch('utils.search_util.requests.post')
    def test_search_success(self, mock_post):
        """Test successful search API call"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"title": "Test Result"}]}
        mock_post.return_value = mock_response

        # Call the function
        result = search("test query")

        # Assertions
        self.assertIsNotNone(result)
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["title"], "Test Result")
        mock_post.assert_called_once()

    @patch('utils.search_util.requests.post')
    def test_search_failure(self, mock_post):
        """Test failed search API call"""
        # Mock API response to raise an exception
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        # Call the function and assert that it returns None
        result = search("test query")
        self.assertIsNone(result)

    @patch('utils.search_util.requests.post')
    def test_find_similar_success(self, mock_post):
        """Test successful find_similar API call"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"title": "Similar Result"}]}
        mock_post.return_value = mock_response

        result = find_similar("http://example.com")

        self.assertIsNotNone(result)
        self.assertIn("results", result)
        self.assertEqual(result["results"][0]["title"], "Similar Result")
        mock_post.assert_called_once()

    @patch('utils.search_util.requests.post')
    def test_get_contents_success(self, mock_post):
        """Test successful get_contents API call"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"contents": [{"content": "Test Content"}]}
        mock_post.return_value = mock_response

        result = get_contents(["test_id_1"])

        self.assertIsNotNone(result)
        self.assertIn("contents", result)
        self.assertEqual(result["contents"][0]["content"], "Test Content")
        mock_post.assert_called_once()

if __name__ == '__main__':
    unittest.main()

