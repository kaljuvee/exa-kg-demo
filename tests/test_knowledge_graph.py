import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.knowledge_graph import KnowledgeGraphBuilder, create_subject_predicate_object_triples

class TestKnowledgeGraph(unittest.TestCase):

    def setUp(self):
        self.builder = KnowledgeGraphBuilder(max_depth=2, max_results_per_level=2)

    @patch('utils.knowledge_graph.search')
    @patch('utils.knowledge_graph.find_similar')
    def test_build_graph_from_search(self, mock_find_similar, mock_search):
        # Mock API responses
        mock_search.return_value = {
            "results": [
                {"title": "Root Node 1", "url": "http://root1.com", "text": "Content with AI and ML"},
                {"title": "Root Node 2", "url": "http://root2.com", "text": "Content about Python"}
            ]
        }
        mock_find_similar.return_value = {
            "results": [
                {"title": "Similar Node 1", "url": "http://similar1.com", "text": "More on AI"}
            ]
        }

        # Build graph
        graph_data = self.builder.build_graph("test query", input_type="search")

        # Assertions
        self.assertIn("nodes", graph_data)
        self.assertIn("edges", graph_data)
        self.assertGreater(len(graph_data["nodes"]), 0)
        self.assertGreater(len(graph_data["edges"]), 0)
        self.assertEqual(mock_search.call_count, 1)
        self.assertGreaterEqual(mock_find_similar.call_count, 1)

    def test_create_triples(self):
        graph_data = {
            "nodes": [
                {"id": "1", "title": "Node A", "content_type": "article", "author": "John Doe", "domain": "example.com", "entities": ["AI"], "level": 0, "keywords": [], "summary": "", "published_date": ""},
                {"id": "2", "title": "Node B", "content_type": "blog", "level": 1, "author": None, "domain": None, "entities": [], "keywords": [], "summary": "", "published_date": ""}
            ],
            "edges": [
                {"source": "1", "target": "2", "relationship": "similar_to"}
            ]
        }

        triples = create_subject_predicate_object_triples(graph_data)

        self.assertGreater(len(triples), 0)
        self.assertIn(("Node A", "similar_to", "Node B"), triples)
        self.assertIn(("Node A", "is_type", "article"), triples)
        self.assertIn(("Node A", "authored_by", "John Doe"), triples)

if __name__ == '__main__':
    unittest.main()

