import unittest
import json
import os
import sys
from unittest.mock import patch

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.knowledge_graph import KnowledgeGraphBuilder, GraphNode, GraphEdge

class TestKnowledgeGraphBuilderSimple(unittest.TestCase):
    """Test KnowledgeGraphBuilder with real test data - simplified version"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.builder = KnowledgeGraphBuilder(max_depth=2, max_results_per_level=3)
        self.test_data_dir = os.path.join(os.path.dirname(__file__), '..', 'test-data')
        
    def load_test_data(self, filename):
        """Load test data from JSON file"""
        filepath = os.path.join(self.test_data_dir, filename)
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def test_build_graph_with_search_query(self):
        """Test building knowledge graph from search query with real data"""
        # Load real test data
        search_data = self.load_test_data('exa_search_openai.json')
        
        # Mock the search function
        with patch('utils.search_util.search') as mock_search:
            mock_search.return_value = search_data
            
            graph_data = self.builder.build_graph("OpenAI", input_type="search")
            
            # Verify graph structure
            self.assertIsInstance(graph_data, dict)
            self.assertIn('nodes', graph_data)
            self.assertIn('edges', graph_data)
            self.assertIn('metadata', graph_data)
            
            # Check that we have nodes
            nodes = graph_data['nodes']
            self.assertGreater(len(nodes), 0)
            
            # Verify node structure
            for node in nodes:
                self.assertIn('id', node)
                self.assertIn('title', node)
                self.assertIn('url', node)
                self.assertIn('level', node)
    
    def test_build_graph_with_url_similarity(self):
        """Test building knowledge graph from URL similarity with real data"""
        # Load real test data
        similar_data = self.load_test_data('exa_similar_openai.json')
        
        # Mock the find_similar function
        with patch('utils.search_util.find_similar') as mock_similar:
            mock_similar.return_value = similar_data
            
            graph_data = self.builder.build_graph("https://openai.com/", input_type="url")
            
            # Verify graph structure
            self.assertIsInstance(graph_data, dict)
            self.assertIn('nodes', graph_data)
            self.assertIn('edges', graph_data)
            self.assertIn('metadata', graph_data)
    
    def test_graph_node_creation(self):
        """Test GraphNode dataclass creation"""
        node = GraphNode(
            id="test_id",
            title="Test Title",
            url="https://example.com",
            level=0,
            node_type="root",
            summary="Test summary",
            author="Test Author",
            published_date="2024-01-01",
            content_type="article"
        )
        
        self.assertEqual(node.id, "test_id")
        self.assertEqual(node.title, "Test Title")
        self.assertEqual(node.url, "https://example.com")
        self.assertEqual(node.level, 0)
        self.assertEqual(node.node_type, "root")
        self.assertIsInstance(node.keywords, list)
        self.assertIsInstance(node.entities, list)
    
    def test_graph_edge_creation(self):
        """Test GraphEdge dataclass creation"""
        edge = GraphEdge(
            source="node1",
            target="node2",
            relationship="similar_to",
            weight=0.85,
            metadata={"description": "Test relationship"}
        )
        
        self.assertEqual(edge.source, "node1")
        self.assertEqual(edge.target, "node2")
        self.assertEqual(edge.relationship, "similar_to")
        self.assertEqual(edge.weight, 0.85)
        self.assertEqual(edge.metadata["description"], "Test relationship")
    
    def test_empty_search_results_handling(self):
        """Test handling of empty search results"""
        # Mock empty search results
        with patch('utils.search_util.search') as mock_search:
            mock_search.return_value = {"search_results": [], "query": "test"}
            
            graph_data = self.builder.build_graph("nonexistent query")
            
            # Should return empty graph structure
            self.assertIsInstance(graph_data, dict)
            self.assertIn('nodes', graph_data)
            self.assertIn('edges', graph_data)
            # With empty results, should have no nodes
            self.assertEqual(len(graph_data['nodes']), 0)
            self.assertEqual(len(graph_data['edges']), 0)
    
    def test_graph_reset_functionality(self):
        """Test that graph state is properly reset between builds"""
        # Load test data
        search_data = self.load_test_data('exa_search_openai.json')
        
        # Build first graph
        with patch('utils.search_util.search') as mock_search:
            mock_search.return_value = search_data
            
            graph1 = self.builder.build_graph("OpenAI")
            nodes_count_1 = len(graph1['nodes'])
            
            # Build second graph
            graph2 = self.builder.build_graph("OpenAI")
            nodes_count_2 = len(graph2['nodes'])
            
            # Should have same number of nodes (graph was reset)
            self.assertEqual(nodes_count_1, nodes_count_2)
    
    def test_builder_configuration(self):
        """Test that builder configuration is properly set"""
        builder = KnowledgeGraphBuilder(max_depth=5, max_results_per_level=20)
        
        self.assertEqual(builder.max_depth, 5)
        self.assertEqual(builder.max_results_per_level, 20)
        self.assertIsInstance(builder.nodes, dict)
        self.assertIsInstance(builder.edges, list)
        self.assertIsInstance(builder.visited_urls, set)
    
    def test_data_structure_validation(self):
        """Test that real test data has expected structure"""
        # Validate Exa search data structure
        search_data = self.load_test_data('exa_search_openai.json')
        
        # Check top-level structure
        self.assertIn('search_results', search_data)
        self.assertIn('query', search_data)
        
        # Check search results structure
        for result in search_data['search_results']:
            required_keys = ['id', 'url', 'title', 'score']
            for key in required_keys:
                self.assertIn(key, result, f"Missing key: {key}")
        
        # Validate similar results data structure
        similar_data = self.load_test_data('exa_similar_openai.json')
        
        self.assertIn('similar_results', similar_data)
        self.assertIn('url', similar_data)
        
        for result in similar_data['similar_results']:
            required_keys = ['id', 'url', 'title', 'score']
            for key in required_keys:
                self.assertIn(key, result, f"Missing key: {key}")
        
        # Validate knowledge graph sample structure
        graph_data = self.load_test_data('knowledge_graph_sample.json')
        
        required_keys = ['nodes', 'edges', 'metadata']
        for key in required_keys:
            self.assertIn(key, graph_data, f"Missing key: {key}")
        
        # Check node structure
        for node in graph_data['nodes']:
            required_node_keys = ['id', 'label', 'type', 'level']
            for key in required_node_keys:
                self.assertIn(key, node, f"Missing node key: {key}")
        
        # Check edge structure
        for edge in graph_data['edges']:
            required_edge_keys = ['source', 'target', 'relationship']
            for key in required_edge_keys:
                self.assertIn(key, edge, f"Missing edge key: {key}")
    
    def test_url_domain_extraction(self):
        """Test URL domain extraction in GraphNode"""
        node = GraphNode(
            id="test",
            title="Test",
            url="https://www.example.com/path/to/page",
            level=0,
            node_type="root"
        )
        
        # Domain should be extracted automatically
        self.assertEqual(node.domain, "www.example.com")
    
    def test_node_with_keywords_and_entities(self):
        """Test GraphNode with keywords and entities"""
        node = GraphNode(
            id="test",
            title="OpenAI Research",
            url="https://openai.com/research",
            level=0,
            node_type="root",
            keywords=["AI", "research", "GPT"],
            entities=["OpenAI", "artificial intelligence"]
        )
        
        self.assertEqual(len(node.keywords), 3)
        self.assertEqual(len(node.entities), 2)
        self.assertIn("AI", node.keywords)
        self.assertIn("OpenAI", node.entities)

if __name__ == '__main__':
    unittest.main()
