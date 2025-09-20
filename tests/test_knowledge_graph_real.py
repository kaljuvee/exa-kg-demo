import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.knowledge_graph import KnowledgeGraphBuilder
from utils import search_util

class TestKnowledgeGraphBuilderReal(unittest.TestCase):
    """Test KnowledgeGraphBuilder with real test data instead of mocks"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.builder = KnowledgeGraphBuilder()
        self.test_data_dir = os.path.join(os.path.dirname(__file__), '..', 'test-data')
        
    def load_test_data(self, filename):
        """Load test data from JSON file"""
        filepath = os.path.join(self.test_data_dir, filename)
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def test_build_graph_from_company_with_real_data(self):
        """Test building knowledge graph from company name with real data"""
        # Load real test data
        search_data = self.load_test_data('exa_search_openai.json')
        similar_data = self.load_test_data('exa_similar_openai.json')
        
        # Mock the search functions
        with patch('utils.search_util.search') as mock_search, \
             patch('utils.search_util.find_similar') as mock_similar:
            
            mock_search.return_value = search_data
            mock_similar.return_value = similar_data
            graph_data = self.builder.build_graph_from_company(
                company_name="OpenAI",
                max_depth=2,
                results_per_level=3
            )
        
        # Verify graph structure
        self.assertIsInstance(graph_data, dict)
        self.assertIn('nodes', graph_data)
        self.assertIn('edges', graph_data)
        self.assertIn('metadata', graph_data)
        
        # Check nodes
        nodes = graph_data['nodes']
        self.assertGreater(len(nodes), 0)
        
        # Verify root node
        root_nodes = [n for n in nodes if n.get('level') == 0]
        self.assertEqual(len(root_nodes), 1)
        root_node = root_nodes[0]
        self.assertEqual(root_node['title'], 'OpenAI')
        self.assertEqual(root_node['url'], 'https://openai.com/')
        
        # Check edges
        edges = graph_data['edges']
        self.assertGreater(len(edges), 0)
        
        # Verify edge structure
        for edge in edges:
            self.assertIn('source', edge)
            self.assertIn('target', edge)
            self.assertIn('relationship', edge)
    
    def test_build_graph_from_url_with_real_data(self):
        """Test building knowledge graph from URL with real data"""
        # Load real test data
        similar_data = self.load_test_data('exa_similar_openai.json')
        
        # Mock the search client
        mock_client = MagicMock(spec=ExaSearchClient)
        mock_client.find_similar.return_value = similar_data['similar_results']
        
        # Patch the search client in the builder
        with patch.object(self.builder, 'search_client', mock_client):
            graph_data = self.builder.build_graph_from_url(
                url="https://openai.com/",
                max_depth=2,
                results_per_level=3
            )
        
        # Verify graph structure
        self.assertIsInstance(graph_data, dict)
        self.assertIn('nodes', graph_data)
        self.assertIn('edges', graph_data)
        
        # Check that we have nodes from similar results
        nodes = graph_data['nodes']
        self.assertGreater(len(nodes), 0)
        
        # Verify we have expected similar companies
        node_titles = [n['title'] for n in nodes]
        self.assertIn('Anthropic', node_titles)
        self.assertIn('Google DeepMind', node_titles)
    
    def test_create_triples_with_real_data(self):
        """Test triple creation with real graph data"""
        # Load real knowledge graph data
        graph_data = self.load_test_data('knowledge_graph_sample.json')
        
        triples = self.builder.create_triples(graph_data)
        
        # Verify triples structure
        self.assertIsInstance(triples, list)
        self.assertGreater(len(triples), 0)
        
        # Check triple format
        for triple in triples:
            self.assertIsInstance(triple, dict)
            self.assertIn('subject', triple)
            self.assertIn('predicate', triple)
            self.assertIn('object', triple)
            
            # Verify content
            self.assertIsInstance(triple['subject'], str)
            self.assertIsInstance(triple['predicate'], str)
            self.assertIsInstance(triple['object'], str)
    
    def test_extract_entities_with_real_content(self):
        """Test entity extraction with real content"""
        # Real content from OpenAI
        content = "OpenAI is an AI research and deployment company. Our mission is to ensure that artificial general intelligence benefits all of humanity. We're the creators of GPT-4, DALL-E, and other cutting-edge AI systems."
        
        entities = self.builder.extract_entities(content)
        
        # Verify entities
        self.assertIsInstance(entities, list)
        self.assertGreater(len(entities), 0)
        
        # Check for expected entities
        entity_text = ' '.join(entities).lower()
        self.assertIn('openai', entity_text)
        self.assertIn('ai', entity_text)
    
    def test_extract_keywords_with_real_content(self):
        """Test keyword extraction with real content"""
        # Real content from AI companies
        content = "Anthropic is an AI safety company focused on developing safe, beneficial, and understandable AI systems. Claude is our AI assistant that can help with analysis, writing, math, coding, and creative tasks."
        
        keywords = self.builder.extract_keywords(content)
        
        # Verify keywords
        self.assertIsInstance(keywords, list)
        self.assertGreater(len(keywords), 0)
        
        # Check for expected keywords
        keyword_text = ' '.join(keywords).lower()
        self.assertIn('ai', keyword_text)
        self.assertIn('safety', keyword_text)
    
    def test_graph_metadata_generation(self):
        """Test that graph metadata is properly generated"""
        # Load real test data
        search_data = self.load_test_data('exa_search_openai.json')
        
        # Mock the search client
        mock_client = MagicMock(spec=ExaSearchClient)
        mock_client.search.return_value = search_data['search_results']
        mock_client.find_similar.return_value = []
        
        # Patch the search client in the builder
        with patch.object(self.builder, 'search_client', mock_client):
            graph_data = self.builder.build_graph_from_company(
                company_name="OpenAI",
                max_depth=1,
                results_per_level=3
            )
        
        # Check metadata
        metadata = graph_data['metadata']
        self.assertIn('total_nodes', metadata)
        self.assertIn('total_edges', metadata)
        self.assertIn('levels', metadata)
        self.assertIn('domains', metadata)
        self.assertIn('created_at', metadata)
        self.assertIn('query', metadata)
        
        # Verify metadata values
        self.assertEqual(metadata['query'], 'OpenAI')
        self.assertGreater(metadata['total_nodes'], 0)
        self.assertIsInstance(metadata['domains'], list)
    
    def test_node_color_assignment(self):
        """Test that nodes are assigned appropriate colors by level"""
        # Load real test data
        search_data = self.load_test_data('exa_search_openai.json')
        similar_data = self.load_test_data('exa_similar_openai.json')
        
        # Mock the search functions
        with patch('utils.search_util.search') as mock_search, \
             patch('utils.search_util.find_similar') as mock_similar:
            
            mock_search.return_value = search_data
            mock_similar.return_value = similar_data
            graph_data = self.builder.build_graph_from_company(
                company_name="OpenAI",
                max_depth=2,
                results_per_level=2
            )
        
        # Check node colors
        nodes = graph_data['nodes']
        for node in nodes:
            self.assertIn('color', node)
            self.assertIn('size', node)
            
            # Level 0 nodes should have different color than level 1
            if node['level'] == 0:
                self.assertEqual(node['color'], '#1f77b4')  # Blue for root
                self.assertGreater(node['size'], 15)  # Larger size for root
            else:
                self.assertEqual(node['color'], '#ff7f0e')  # Orange for others
    
    def test_relationship_types(self):
        """Test that appropriate relationship types are assigned"""
        # Load real knowledge graph data
        graph_data = self.load_test_data('knowledge_graph_sample.json')
        
        edges = graph_data['edges']
        
        # Check relationship types
        relationship_types = set(edge['relationship'] for edge in edges)
        self.assertIn('similar_to', relationship_types)
        
        # Verify edge weights
        for edge in edges:
            if 'weight' in edge:
                self.assertGreater(edge['weight'], 0)
                self.assertLessEqual(edge['weight'], 1.0)
    
    def test_domain_extraction(self):
        """Test that domains are properly extracted from URLs"""
        # Test URLs from real data
        test_urls = [
            "https://openai.com/",
            "https://www.anthropic.com/",
            "https://deepmind.google/",
            "https://www.microsoft.com/en-us/ai"
        ]
        
        for url in test_urls:
            domain = self.builder._extract_domain(url)
            self.assertIsInstance(domain, str)
            self.assertNotIn('http', domain)
            self.assertNotIn('www.', domain)
    
    def test_data_structure_validation(self):
        """Test that real test data has expected structure"""
        # Validate knowledge graph sample structure
        graph_data = self.load_test_data('knowledge_graph_sample.json')
        
        # Check top-level structure
        required_keys = ['nodes', 'edges', 'metadata']
        for key in required_keys:
            self.assertIn(key, graph_data, f"Missing key: {key}")
        
        # Check node structure
        for node in graph_data['nodes']:
            required_node_keys = ['id', 'label', 'type', 'level', 'title', 'url']
            for key in required_node_keys:
                self.assertIn(key, node, f"Missing node key: {key}")
        
        # Check edge structure
        for edge in graph_data['edges']:
            required_edge_keys = ['source', 'target', 'relationship']
            for key in required_edge_keys:
                self.assertIn(key, edge, f"Missing edge key: {key}")
        
        # Check metadata structure
        metadata = graph_data['metadata']
        required_metadata_keys = ['total_nodes', 'total_edges', 'levels', 'domains']
        for key in required_metadata_keys:
            self.assertIn(key, metadata, f"Missing metadata key: {key}")

if __name__ == '__main__':
    unittest.main()
