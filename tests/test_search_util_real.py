import unittest
import json
import os
import sys
from unittest.mock import patch
import requests

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils import search_util

class TestSearchUtilReal(unittest.TestCase):
    """Test search_util functions with real test data instead of mocks"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_data_dir = os.path.join(os.path.dirname(__file__), '..', 'test-data')
        
    def load_test_data(self, filename):
        """Load test data from JSON file"""
        filepath = os.path.join(self.test_data_dir, filename)
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def test_search_with_real_data(self):
        """Test search functionality with real API response data"""
        # Load real test data
        test_data = self.load_test_data('exa_search_openai.json')
        
        # Mock the requests.post call
        with patch('requests.post') as mock_post:
            mock_response = mock_post.return_value
            mock_response.json.return_value = test_data
            mock_response.raise_for_status.return_value = None
            
            results = search_util.search("OpenAI", num_results=3)
            
            # Verify the results structure
            self.assertIsNotNone(results)
            self.assertIn('search_results', results)
            
            search_results = results['search_results']
            self.assertEqual(len(search_results), 3)
            
            # Check first result structure
            first_result = search_results[0]
            self.assertIn('id', first_result)
            self.assertIn('url', first_result)
            self.assertIn('title', first_result)
            self.assertIn('score', first_result)
            self.assertEqual(first_result['title'], 'OpenAI')
            self.assertEqual(first_result['url'], 'https://openai.com/')
            self.assertGreater(first_result['score'], 0.9)
    
    def test_find_similar_with_real_data(self):
        """Test find_similar functionality with real API response data"""
        # Load real test data
        test_data = self.load_test_data('exa_similar_openai.json')
        
        # Mock the requests.post call
        with patch('requests.post') as mock_post:
            mock_response = mock_post.return_value
            mock_response.json.return_value = test_data
            mock_response.raise_for_status.return_value = None
            
            results = search_util.find_similar("https://openai.com/", num_results=3)
            
            # Verify the results structure
            self.assertIsNotNone(results)
            self.assertIn('similar_results', results)
            
            similar_results = results['similar_results']
            self.assertEqual(len(similar_results), 3)
            
            # Check that we get expected similar companies
            titles = [result['title'] for result in similar_results]
            self.assertIn('Anthropic', titles)
            self.assertIn('Google DeepMind', titles)
            self.assertIn('Microsoft AI', titles)
            
            # Verify score ranges
            for result in similar_results:
                self.assertGreater(result['score'], 0.8)
                self.assertLessEqual(result['score'], 1.0)
    
    def test_get_contents_with_real_data(self):
        """Test get_contents functionality with realistic data"""
        # Create realistic content response
        content_data = {
            "results": [
                {
                    "id": "https://openai.com/",
                    "url": "https://openai.com/",
                    "title": "OpenAI",
                    "text": "OpenAI is an AI research and deployment company. Our mission is to ensure that artificial general intelligence benefits all of humanity. We're the creators of GPT-4, DALL-E, and other cutting-edge AI systems.",
                    "author": "OpenAI Team",
                    "published_date": "2024-01-15"
                }
            ]
        }
        
        # Mock the requests.post call
        with patch('requests.post') as mock_post:
            mock_response = mock_post.return_value
            mock_response.json.return_value = content_data
            mock_response.raise_for_status.return_value = None
            
            results = search_util.get_contents(["https://openai.com/"])
            
            # Verify the results
            self.assertIsNotNone(results)
            self.assertIn('results', results)
            
            result_list = results['results']
            self.assertEqual(len(result_list), 1)
            
            result = result_list[0]
            self.assertEqual(result['url'], 'https://openai.com/')
            self.assertIn('text', result)
            self.assertIn('GPT-4', result['text'])
            self.assertIn('DALL-E', result['text'])
    
    def test_error_handling_with_invalid_api_key(self):
        """Test error handling with invalid API key"""
        # Mock a 401 error response
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
            
            result = search_util.search("test query")
            self.assertIsNone(result)
    
    def test_empty_results_handling(self):
        """Test handling of empty search results"""
        empty_data = {
            "search_results": [],
            "autoprompt_string": "No results found",
            "response_time": 0.5
        }
        
        with patch('requests.post') as mock_post:
            mock_response = mock_post.return_value
            mock_response.json.return_value = empty_data
            mock_response.raise_for_status.return_value = None
            
            results = search_util.search("nonexistent query")
            
            self.assertIsNotNone(results)
            self.assertIn('search_results', results)
            self.assertEqual(len(results['search_results']), 0)
    
    def test_data_validation(self):
        """Test that real test data has expected structure"""
        # Test Exa search data structure
        search_data = self.load_test_data('exa_search_openai.json')
        self.assertIn('search_results', search_data)
        self.assertIn('query', search_data)
        self.assertIn('response_time', search_data)
        
        # Test individual result structure
        for result in search_data['search_results']:
            required_fields = ['id', 'url', 'title', 'score']
            for field in required_fields:
                self.assertIn(field, result, f"Missing field: {field}")
        
        # Test similar results data structure
        similar_data = self.load_test_data('exa_similar_openai.json')
        self.assertIn('similar_results', similar_data)
        self.assertIn('url', similar_data)
        
        for result in similar_data['similar_results']:
            required_fields = ['id', 'url', 'title', 'score']
            for field in required_fields:
                self.assertIn(field, result, f"Missing field: {field}")

if __name__ == '__main__':
    unittest.main()
