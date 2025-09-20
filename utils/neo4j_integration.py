"""
Neo4j Integration Module

This module provides functionality to store and query knowledge graphs in a local Neo4j database.
It includes methods to create nodes, relationships, and perform graph queries.
"""

import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import asdict
import os

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Neo4j driver not available. Install with: pip install neo4j")

from .knowledge_graph import GraphNode, GraphEdge


class Neo4jKnowledgeGraph:
    """Neo4j integration for knowledge graph storage and querying"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        """
        Initialize Neo4j connection
        
        Args:
            uri: Neo4j database URI
            user: Database username
            password: Database password
        """
        if not NEO4J_AVAILABLE:
            raise ImportError("Neo4j driver not available. Install with: pip install neo4j")
        
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None
        self.connected = False
        
    def connect(self) -> bool:
        """
        Establish connection to Neo4j database
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            self.connected = False
            return False
    
    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()
            self.connected = False
    
    def clear_database(self):
        """Clear all nodes and relationships from the database"""
        if not self.connected:
            return False
        
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        return True
    
    def import_knowledge_graph(self, graph_data: Dict) -> bool:
        """
        Import a complete knowledge graph into Neo4j
        
        Args:
            graph_data: Graph data dictionary from KnowledgeGraphBuilder
            
        Returns:
            True if import successful, False otherwise
        """
        if not self.connected:
            print("Not connected to Neo4j database")
            return False
        
        try:
            with self.driver.session() as session:
                # Create nodes
                for node_data in graph_data['nodes']:
                    self._create_node(session, node_data)
                
                # Create relationships
                for edge_data in graph_data['edges']:
                    self._create_relationship(session, edge_data)
                
                # Create indexes for better performance
                self._create_indexes(session)
                
            return True
        except Exception as e:
            print(f"Error importing knowledge graph: {e}")
            return False
    
    def _create_node(self, session, node_data: Dict):
        """Create a single node in Neo4j"""
        # Prepare properties, handling lists by converting to strings
        properties = {}
        for key, value in node_data.items():
            if key == 'id':
                continue  # Skip id as it's used for node identification
            elif isinstance(value, list):
                properties[key] = json.dumps(value) if value else "[]"
            elif value is not None:
                properties[key] = str(value)
        
        # Create node with KnowledgeNode label
        query = """
        CREATE (n:KnowledgeNode {id: $id})
        SET n += $properties
        """
        
        session.run(query, id=node_data['id'], properties=properties)
    
    def _create_relationship(self, session, edge_data: Dict):
        """Create a relationship between two nodes"""
        # Sanitize relationship type (Neo4j doesn't allow certain characters)
        rel_type = edge_data['relationship'].upper().replace(' ', '_').replace('-', '_')
        
        # Prepare relationship properties
        properties = {
            'weight': edge_data.get('weight', 1.0),
            'metadata': json.dumps(edge_data.get('metadata', {}))
        }
        
        query = f"""
        MATCH (source:KnowledgeNode {{id: $source_id}})
        MATCH (target:KnowledgeNode {{id: $target_id}})
        CREATE (source)-[r:{rel_type}]->(target)
        SET r += $properties
        """
        
        session.run(query, 
                   source_id=edge_data['source'],
                   target_id=edge_data['target'],
                   properties=properties)
    
    def _create_indexes(self, session):
        """Create indexes for better query performance"""
        indexes = [
            "CREATE INDEX node_id_index IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.id)",
            "CREATE INDEX node_title_index IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.title)",
            "CREATE INDEX node_level_index IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.level)",
            "CREATE INDEX node_domain_index IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.domain)",
            "CREATE INDEX node_content_type_index IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.content_type)"
        ]
        
        for index_query in indexes:
            try:
                session.run(index_query)
            except Exception as e:
                print(f"Warning: Could not create index: {e}")
    
    def query_nodes_by_level(self, level: int) -> List[Dict]:
        """Query nodes by level"""
        if not self.connected:
            return []
        
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n:KnowledgeNode) WHERE n.level = $level RETURN n",
                level=str(level)
            )
            return [dict(record['n']) for record in result]
    
    def query_nodes_by_domain(self, domain: str) -> List[Dict]:
        """Query nodes by domain"""
        if not self.connected:
            return []
        
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n:KnowledgeNode) WHERE n.domain = $domain RETURN n",
                domain=domain
            )
            return [dict(record['n']) for record in result]
    
    def query_nodes_by_content_type(self, content_type: str) -> List[Dict]:
        """Query nodes by content type"""
        if not self.connected:
            return []
        
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n:KnowledgeNode) WHERE n.content_type = $content_type RETURN n",
                content_type=content_type
            )
            return [dict(record['n']) for record in result]
    
    def find_shortest_path(self, source_id: str, target_id: str) -> List[Dict]:
        """Find shortest path between two nodes"""
        if not self.connected:
            return []
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (source:KnowledgeNode {id: $source_id}),
                      (target:KnowledgeNode {id: $target_id}),
                      path = shortestPath((source)-[*]-(target))
                RETURN path
            """, source_id=source_id, target_id=target_id)
            
            paths = []
            for record in result:
                path = record['path']
                path_data = {
                    'nodes': [dict(node) for node in path.nodes],
                    'relationships': [dict(rel) for rel in path.relationships],
                    'length': len(path.relationships)
                }
                paths.append(path_data)
            
            return paths
    
    def get_node_neighbors(self, node_id: str, max_depth: int = 1) -> List[Dict]:
        """Get neighbors of a node up to specified depth"""
        if not self.connected:
            return []
        
        with self.driver.session() as session:
            result = session.run(f"""
                MATCH (n:KnowledgeNode {{id: $node_id}})-[*1..{max_depth}]-(neighbor:KnowledgeNode)
                RETURN DISTINCT neighbor
            """, node_id=node_id)
            
            return [dict(record['neighbor']) for record in result]
    
    def get_most_connected_nodes(self, limit: int = 10) -> List[Dict]:
        """Get nodes with the most connections"""
        if not self.connected:
            return []
        
        with self.driver.session() as session:
            result = session.run(f"""
                MATCH (n:KnowledgeNode)
                OPTIONAL MATCH (n)-[r]-()
                WITH n, count(r) as connections
                ORDER BY connections DESC
                LIMIT {limit}
                RETURN n, connections
            """)
            
            return [{'node': dict(record['n']), 'connections': record['connections']} 
                   for record in result]
    
    def search_nodes_by_text(self, search_text: str) -> List[Dict]:
        """Search nodes by text content in title or summary"""
        if not self.connected:
            return []
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:KnowledgeNode)
                WHERE toLower(n.title) CONTAINS toLower($search_text)
                   OR toLower(n.summary) CONTAINS toLower($search_text)
                RETURN n
            """, search_text=search_text)
            
            return [dict(record['n']) for record in result]
    
    def get_relationship_types(self) -> List[str]:
        """Get all relationship types in the database"""
        if not self.connected:
            return []
        
        with self.driver.session() as session:
            result = session.run("CALL db.relationshipTypes()")
            return [record[0] for record in result]
    
    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        if not self.connected:
            return {}
        
        with self.driver.session() as session:
            # Count nodes
            node_count = session.run("MATCH (n:KnowledgeNode) RETURN count(n) as count").single()['count']
            
            # Count relationships
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
            
            # Get relationship type distribution
            rel_types = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
            """)
            rel_distribution = {record['rel_type']: record['count'] for record in rel_types}
            
            # Get level distribution
            level_dist = session.run("""
                MATCH (n:KnowledgeNode)
                WHERE n.level IS NOT NULL
                RETURN n.level as level, count(n) as count
                ORDER BY level
            """)
            level_distribution = {record['level']: record['count'] for record in level_dist}
            
            return {
                'node_count': node_count,
                'relationship_count': rel_count,
                'relationship_types': rel_distribution,
                'level_distribution': level_distribution
            }
    
    def export_to_cypher(self, output_file: str) -> bool:
        """Export the entire graph as Cypher CREATE statements"""
        if not self.connected:
            return False
        
        try:
            with open(output_file, 'w') as f:
                with self.driver.session() as session:
                    # Export nodes
                    f.write("// Create nodes\n")
                    nodes = session.run("MATCH (n:KnowledgeNode) RETURN n")
                    for record in nodes:
                        node = record['n']
                        properties = dict(node)
                        node_id = properties.pop('id')
                        
                        # Format properties for Cypher
                        prop_strings = []
                        for key, value in properties.items():
                            if value is not None:
                                if isinstance(value, str):
                                    prop_strings.append(f"{key}: '{value.replace(chr(39), chr(39)+chr(39))}'")
                                else:
                                    prop_strings.append(f"{key}: {value}")
                        
                        props_str = ', '.join(prop_strings)
                        f.write(f"CREATE (n_{node_id.replace('-', '_')}:KnowledgeNode {{id: '{node_id}', {props_str}}});\n")
                    
                    # Export relationships
                    f.write("\n// Create relationships\n")
                    rels = session.run("MATCH (a)-[r]->(b) RETURN a.id as source, b.id as target, type(r) as rel_type, properties(r) as props")
                    for record in rels:
                        source_id = record['source'].replace('-', '_')
                        target_id = record['target'].replace('-', '_')
                        rel_type = record['rel_type']
                        props = record['props']
                        
                        prop_strings = []
                        for key, value in props.items():
                            if value is not None:
                                if isinstance(value, str):
                                    prop_strings.append(f"{key}: '{value.replace(chr(39), chr(39)+chr(39))}'")
                                else:
                                    prop_strings.append(f"{key}: {value}")
                        
                        props_str = ', '.join(prop_strings)
                        if props_str:
                            f.write(f"MATCH (a:KnowledgeNode {{id: '{record['source']}'}}), (b:KnowledgeNode {{id: '{record['target']}'}}) CREATE (a)-[:{rel_type} {{{props_str}}}]->(b);\n")
                        else:
                            f.write(f"MATCH (a:KnowledgeNode {{id: '{record['source']}'}}), (b:KnowledgeNode {{id: '{record['target']}'}}) CREATE (a)-[:{rel_type}]->(b);\n")
            
            return True
        except Exception as e:
            print(f"Error exporting to Cypher: {e}")
            return False


def setup_local_neo4j():
    """
    Instructions for setting up a local Neo4j database
    """
    instructions = """
    To set up a local Neo4j database:
    
    1. Download Neo4j Desktop from: https://neo4j.com/download/
    2. Install and create a new database
    3. Set password (default username is 'neo4j')
    4. Start the database
    5. The default connection is: bolt://localhost:7687
    
    Alternative - Using Docker:
    docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest
    
    Then access the browser interface at: http://localhost:7474
    """
    return instructions


def create_sample_queries():
    """
    Return sample Cypher queries for knowledge graph analysis
    """
    queries = {
        "Find all research papers": "MATCH (n:KnowledgeNode) WHERE n.content_type = 'research_paper' RETURN n",
        "Find nodes with most connections": """
            MATCH (n:KnowledgeNode)
            OPTIONAL MATCH (n)-[r]-()
            WITH n, count(r) as connections
            ORDER BY connections DESC
            LIMIT 10
            RETURN n.title, connections
        """,
        "Find shortest path between two nodes": """
            MATCH (a:KnowledgeNode {title: 'Node A'}),
                  (b:KnowledgeNode {title: 'Node B'}),
                  path = shortestPath((a)-[*]-(b))
            RETURN path
        """,
        "Find nodes by domain": "MATCH (n:KnowledgeNode) WHERE n.domain = 'arxiv.org' RETURN n",
        "Find similar content relationships": "MATCH (a)-[r:SIMILAR_TO]->(b) RETURN a.title, b.title, r.weight",
        "Get level distribution": """
            MATCH (n:KnowledgeNode)
            WHERE n.level IS NOT NULL
            RETURN n.level as level, count(n) as count
            ORDER BY level
        """,
        "Find nodes mentioning specific entities": """
            MATCH (n:KnowledgeNode)
            WHERE n.entities CONTAINS 'AI'
            RETURN n.title, n.entities
        """
    }
    return queries
