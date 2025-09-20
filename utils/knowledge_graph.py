"""
Knowledge Graph Builder Module

This module provides functionality to build knowledge graphs from Exa.ai search results
with configurable depth and relationship extraction capabilities.
"""

import json
import re
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib

from .search_util import search, find_similar, get_contents


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph"""
    id: str
    title: str
    url: str
    level: int
    node_type: str  # 'root', 'primary', 'secondary', 'tertiary'
    summary: str = ""
    author: str = ""
    published_date: str = ""
    domain: str = ""
    content_type: str = ""  # 'article', 'research_paper', 'company_page', etc.
    keywords: List[str] = None
    entities: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.entities is None:
            self.entities = []
        
        # Extract domain from URL
        if self.url and not self.domain:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(self.url)
                self.domain = parsed.netloc
            except:
                self.domain = ""


@dataclass
class GraphEdge:
    """Represents an edge/relationship in the knowledge graph"""
    source: str
    target: str
    relationship: str
    weight: float = 1.0
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class KnowledgeGraphBuilder:
    """Main class for building knowledge graphs from Exa.ai data"""
    
    def __init__(self, max_depth: int = 3, max_results_per_level: int = 10):
        self.max_depth = max_depth
        self.max_results_per_level = max_results_per_level
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.visited_urls: Set[str] = set()
        self.entity_cache: Dict[str, List[str]] = {}
        
    def build_graph(self, query: str, input_type: str = "search") -> Dict:
        """
        Build a knowledge graph starting from a query or URL
        
        Args:
            query: Search query or URL
            input_type: 'search' for text query, 'url' for URL-based similarity search
            
        Returns:
            Dictionary containing nodes, edges, and metadata
        """
        self._reset_graph()
        
        # Level 0: Initial search
        if input_type == "search":
            initial_results = search(query, num_results=self.max_results_per_level)
        else:
            initial_results = find_similar(query, num_results=self.max_results_per_level)
        
        if not initial_results or 'results' not in initial_results:
            return self._export_graph()
        
        # Process initial results
        root_nodes = self._process_search_results(initial_results['results'], level=0, node_type='root')
        
        # Build deeper levels
        for level in range(1, self.max_depth):
            self._build_level(level)
        
        # Extract relationships and enhance graph
        self._extract_relationships()
        self._calculate_node_importance()
        
        return self._export_graph()
    
    def _reset_graph(self):
        """Reset the graph state"""
        self.nodes.clear()
        self.edges.clear()
        self.visited_urls.clear()
        self.entity_cache.clear()
    
    def _process_search_results(self, results: List[Dict], level: int, node_type: str, parent_id: str = None) -> List[str]:
        """Process search results and create nodes"""
        node_ids = []
        
        for i, result in enumerate(results):
            url = result.get('url', '')
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
            
            self.visited_urls.add(url)
            
            # Create unique node ID
            node_id = self._generate_node_id(result.get('title', ''), url, level)
            
            # Extract entities and keywords
            text_content = result.get('text', '') + ' ' + result.get('summary', '')
            entities = self._extract_entities(text_content)
            keywords = self._extract_keywords(text_content)
            
            # Determine content type
            content_type = self._classify_content_type(result)
            
            # Create node
            node = GraphNode(
                id=node_id,
                title=result.get('title', 'Unknown Title'),
                url=url,
                level=level,
                node_type=node_type,
                summary=result.get('summary', ''),
                author=result.get('author', ''),
                published_date=result.get('publishedDate', ''),
                content_type=content_type,
                keywords=keywords,
                entities=entities
            )
            
            self.nodes[node_id] = node
            node_ids.append(node_id)
            
            # Create edge to parent if exists
            if parent_id and parent_id in self.nodes:
                edge = GraphEdge(
                    source=parent_id,
                    target=node_id,
                    relationship='similar_to',
                    weight=self._calculate_similarity_weight(result),
                    metadata={'level_transition': f"{level-1}_to_{level}"}
                )
                self.edges.append(edge)
        
        return node_ids
    
    def _build_level(self, level: int):
        """Build a specific level of the graph"""
        if level == 0:
            return
        
        # Get nodes from previous level
        prev_level_nodes = [node for node in self.nodes.values() if node.level == level - 1]
        
        # Limit nodes to explore to avoid API limits
        nodes_to_explore = prev_level_nodes[:min(3, len(prev_level_nodes))]
        
        for parent_node in nodes_to_explore:
            if not parent_node.url:
                continue
            
            # Find similar content
            similar_results = find_similar(parent_node.url, num_results=min(5, self.max_results_per_level))
            
            if similar_results and 'results' in similar_results:
                node_type = self._get_node_type_for_level(level)
                self._process_search_results(
                    similar_results['results'], 
                    level=level, 
                    node_type=node_type,
                    parent_id=parent_node.id
                )
    
    def _extract_relationships(self):
        """Extract additional relationships between nodes based on content analysis"""
        nodes_list = list(self.nodes.values())
        
        for i, node1 in enumerate(nodes_list):
            for j, node2 in enumerate(nodes_list[i+1:], i+1):
                # Skip if nodes are already connected
                if self._are_nodes_connected(node1.id, node2.id):
                    continue
                
                # Check for entity overlap
                common_entities = set(node1.entities) & set(node2.entities)
                if len(common_entities) >= 2:  # At least 2 common entities
                    edge = GraphEdge(
                        source=node1.id,
                        target=node2.id,
                        relationship='shares_entities',
                        weight=len(common_entities) * 0.3,
                        metadata={'common_entities': list(common_entities)}
                    )
                    self.edges.append(edge)
                
                # Check for keyword overlap
                common_keywords = set(node1.keywords) & set(node2.keywords)
                if len(common_keywords) >= 3:  # At least 3 common keywords
                    edge = GraphEdge(
                        source=node1.id,
                        target=node2.id,
                        relationship='shares_keywords',
                        weight=len(common_keywords) * 0.2,
                        metadata={'common_keywords': list(common_keywords)}
                    )
                    self.edges.append(edge)
                
                # Check for same domain
                if node1.domain and node2.domain and node1.domain == node2.domain:
                    edge = GraphEdge(
                        source=node1.id,
                        target=node2.id,
                        relationship='same_domain',
                        weight=0.5,
                        metadata={'domain': node1.domain}
                    )
                    self.edges.append(edge)
                
                # Check for author relationship
                if (node1.author and node2.author and 
                    node1.author.lower() == node2.author.lower()):
                    edge = GraphEdge(
                        source=node1.id,
                        target=node2.id,
                        relationship='same_author',
                        weight=0.8,
                        metadata={'author': node1.author}
                    )
                    self.edges.append(edge)
    
    def _calculate_node_importance(self):
        """Calculate importance scores for nodes based on connections and content"""
        # Calculate degree centrality
        node_degrees = {}
        for node_id in self.nodes:
            degree = sum(1 for edge in self.edges if edge.source == node_id or edge.target == node_id)
            node_degrees[node_id] = degree
        
        # Update node metadata with importance scores
        for node_id, node in self.nodes.items():
            importance_score = (
                node_degrees.get(node_id, 0) * 0.4 +  # Degree centrality
                len(node.entities) * 0.1 +  # Entity richness
                len(node.keywords) * 0.05 +  # Keyword richness
                (1.0 if node.level == 0 else 0.5 / (node.level + 1))  # Level importance
            )
            
            # Store in node metadata (we'll add this to the dataclass if needed)
            if not hasattr(node, 'importance_score'):
                node.importance_score = importance_score
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities from text (simplified implementation)"""
        if not text:
            return []
        
        # Cache results to avoid reprocessing
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.entity_cache:
            return self.entity_cache[text_hash]
        
        # Simple entity extraction using patterns
        entities = []
        
        # Company names (capitalized words, often with Inc, Corp, Ltd)
        company_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|Corp|Ltd|LLC|Co)\.?)?(?=\s|$|[.,;])'
        companies = re.findall(company_pattern, text)
        entities.extend([c.strip() for c in companies if len(c.strip()) > 2])
        
        # Technology terms
        tech_terms = ['AI', 'ML', 'API', 'LLM', 'GPT', 'blockchain', 'cryptocurrency', 'fintech', 'SaaS']
        for term in tech_terms:
            if term.lower() in text.lower():
                entities.append(term)
        
        # Remove duplicates and limit
        entities = list(set(entities))[:10]
        
        self.entity_cache[text_hash] = entities
        return entities
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (simplified implementation)"""
        if not text:
            return []
        
        # Simple keyword extraction
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Filter out common words
        stop_words = {'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'were', 'said', 'each', 'which', 'their', 'time', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also', 'your', 'work', 'life', 'only', 'can', 'still', 'should', 'after', 'being', 'now', 'made', 'before', 'here', 'through', 'when', 'where', 'much', 'some', 'these', 'many', 'would', 'there'}
        
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        
        # Count frequency and return top keywords
        from collections import Counter
        keyword_counts = Counter(keywords)
        return [word for word, count in keyword_counts.most_common(15)]
    
    def _classify_content_type(self, result: Dict) -> str:
        """Classify the type of content based on URL and metadata"""
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()
        
        if 'arxiv.org' in url or 'research' in title or 'paper' in title:
            return 'research_paper'
        elif 'github.com' in url:
            return 'code_repository'
        elif 'linkedin.com' in url:
            return 'profile'
        elif 'news' in url or 'blog' in url:
            return 'article'
        elif any(term in title for term in ['company', 'corp', 'inc', 'about us']):
            return 'company_page'
        else:
            return 'webpage'
    
    def _calculate_similarity_weight(self, result: Dict) -> float:
        """Calculate similarity weight based on result metadata"""
        # Use highlight scores if available
        highlight_scores = result.get('highlightScores', [])
        if highlight_scores:
            return max(highlight_scores)
        
        # Default weight
        return 0.5
    
    def _get_node_type_for_level(self, level: int) -> str:
        """Get node type based on level"""
        type_mapping = {
            0: 'root',
            1: 'primary',
            2: 'secondary',
            3: 'tertiary',
        }
        return type_mapping.get(level, 'tertiary')
    
    def _are_nodes_connected(self, node1_id: str, node2_id: str) -> bool:
        """Check if two nodes are already connected"""
        for edge in self.edges:
            if ((edge.source == node1_id and edge.target == node2_id) or
                (edge.source == node2_id and edge.target == node1_id)):
                return True
        return False
    
    def _generate_node_id(self, title: str, url: str, level: int) -> str:
        """Generate a unique node ID"""
        # Create a hash from title and URL for uniqueness
        content = f"{title}_{url}_{level}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _export_graph(self) -> Dict:
        """Export the graph as a dictionary"""
        return {
            'nodes': [asdict(node) for node in self.nodes.values()],
            'edges': [asdict(edge) for edge in self.edges],
            'metadata': {
                'total_nodes': len(self.nodes),
                'total_edges': len(self.edges),
                'max_depth': self.max_depth,
                'levels': {
                    level: len([n for n in self.nodes.values() if n.level == level])
                    for level in range(self.max_depth)
                },
                'content_types': {
                    content_type: len([n for n in self.nodes.values() if n.content_type == content_type])
                    for content_type in set(n.content_type for n in self.nodes.values())
                },
                'created_at': datetime.now().isoformat()
            }
        }
    
    def get_graph_statistics(self) -> Dict:
        """Get statistics about the current graph"""
        if not self.nodes:
            return {}
        
        return {
            'node_count': len(self.nodes),
            'edge_count': len(self.edges),
            'levels': max(node.level for node in self.nodes.values()) + 1,
            'domains': len(set(node.domain for node in self.nodes.values() if node.domain)),
            'content_types': len(set(node.content_type for node in self.nodes.values())),
            'avg_entities_per_node': sum(len(node.entities) for node in self.nodes.values()) / len(self.nodes),
            'avg_keywords_per_node': sum(len(node.keywords) for node in self.nodes.values()) / len(self.nodes)
        }


def create_subject_predicate_object_triples(graph_data: Dict) -> List[Tuple[str, str, str]]:
    """
    Convert graph data into subject-predicate-object triples for knowledge representation
    
    Args:
        graph_data: Graph data dictionary from KnowledgeGraphBuilder
        
    Returns:
        List of (subject, predicate, object) tuples
    """
    triples = []
    
    nodes = {node['id']: node for node in graph_data['nodes']}
    
    # Create triples from edges
    for edge in graph_data['edges']:
        source_node = nodes.get(edge['source'])
        target_node = nodes.get(edge['target'])
        
        if source_node and target_node:
            subject = source_node['title']
            predicate = edge['relationship']
            object_val = target_node['title']
            
            triples.append((subject, predicate, object_val))
    
    # Create triples from node properties
    for node in graph_data['nodes']:
        title = node['title']
        
        # Type triples
        if node['content_type']:
            triples.append((title, 'is_type', node['content_type']))
        
        # Author triples
        if node['author']:
            triples.append((title, 'authored_by', node['author']))
        
        # Domain triples
        if node['domain']:
            triples.append((title, 'hosted_on', node['domain']))
        
        # Entity triples
        for entity in node.get('entities', []):
            triples.append((title, 'mentions', entity))
        
        # Level triples
        triples.append((title, 'at_level', str(node['level'])))
    
    return triples
