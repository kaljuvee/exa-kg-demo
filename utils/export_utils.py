"""
Export Utilities Module

This module provides comprehensive export functionality for knowledge graphs
in various formats including JSON, CSV, GraphML, GEXF, and others.
"""

import json
import csv
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
import os

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    print("NetworkX not available. Install with: pip install networkx")


class KnowledgeGraphExporter:
    """Comprehensive exporter for knowledge graphs"""
    
    def __init__(self, graph_data: Dict):
        """
        Initialize exporter with graph data
        
        Args:
            graph_data: Graph data dictionary from KnowledgeGraphBuilder
        """
        self.graph_data = graph_data
        self.nodes = graph_data.get('nodes', [])
        self.edges = graph_data.get('edges', [])
        self.metadata = graph_data.get('metadata', {})
    
    def export_json(self, output_path: str, pretty: bool = True) -> bool:
        """
        Export graph as JSON
        
        Args:
            output_path: Output file path
            pretty: Whether to format JSON with indentation
            
        Returns:
            True if export successful
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(self.graph_data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(self.graph_data, f, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting JSON: {e}")
            return False
    
    def export_csv_nodes(self, output_path: str) -> bool:
        """Export nodes as CSV"""
        try:
            if not self.nodes:
                return False
            
            # Flatten nested data
            flattened_nodes = []
            for node in self.nodes:
                flat_node = {}
                for key, value in node.items():
                    if isinstance(value, list):
                        flat_node[key] = '; '.join(map(str, value)) if value else ''
                    elif isinstance(value, dict):
                        flat_node[key] = json.dumps(value)
                    else:
                        flat_node[key] = str(value) if value is not None else ''
                flattened_nodes.append(flat_node)
            
            df = pd.DataFrame(flattened_nodes)
            df.to_csv(output_path, index=False, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error exporting nodes CSV: {e}")
            return False
    
    def export_csv_edges(self, output_path: str) -> bool:
        """Export edges as CSV"""
        try:
            if not self.edges:
                return False
            
            # Flatten edge data
            flattened_edges = []
            for edge in self.edges:
                flat_edge = {}
                for key, value in edge.items():
                    if isinstance(value, dict):
                        flat_edge[key] = json.dumps(value)
                    else:
                        flat_edge[key] = str(value) if value is not None else ''
                flattened_edges.append(flat_edge)
            
            df = pd.DataFrame(flattened_edges)
            df.to_csv(output_path, index=False, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error exporting edges CSV: {e}")
            return False
    
    def export_triples_tsv(self, output_path: str) -> bool:
        """Export as subject-predicate-object triples in TSV format"""
        try:
            from .knowledge_graph import create_subject_predicate_object_triples
            
            triples = create_subject_predicate_object_triples(self.graph_data)
            
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f, delimiter='\t')
                writer.writerow(['Subject', 'Predicate', 'Object'])
                writer.writerows(triples)
            
            return True
        except Exception as e:
            print(f"Error exporting triples TSV: {e}")
            return False
    
    def export_graphml(self, output_path: str) -> bool:
        """Export as GraphML format (XML-based graph format)"""
        if not NETWORKX_AVAILABLE:
            print("NetworkX required for GraphML export")
            return False
        
        try:
            # Create NetworkX graph
            G = nx.DiGraph()
            
            # Add nodes
            for node in self.nodes:
                node_attrs = {}
                for key, value in node.items():
                    if key != 'id':
                        if isinstance(value, (list, dict)):
                            node_attrs[key] = json.dumps(value)
                        else:
                            node_attrs[key] = str(value) if value is not None else ''
                
                G.add_node(node['id'], **node_attrs)
            
            # Add edges
            for edge in self.edges:
                edge_attrs = {}
                for key, value in edge.items():
                    if key not in ['source', 'target']:
                        if isinstance(value, dict):
                            edge_attrs[key] = json.dumps(value)
                        else:
                            edge_attrs[key] = str(value) if value is not None else ''
                
                G.add_edge(edge['source'], edge['target'], **edge_attrs)
            
            # Export to GraphML
            nx.write_graphml(G, output_path)
            return True
        except Exception as e:
            print(f"Error exporting GraphML: {e}")
            return False
    
    def export_gexf(self, output_path: str) -> bool:
        """Export as GEXF format (Graph Exchange XML Format)"""
        if not NETWORKX_AVAILABLE:
            print("NetworkX required for GEXF export")
            return False
        
        try:
            # Create NetworkX graph
            G = nx.DiGraph()
            
            # Add nodes with attributes
            for node in self.nodes:
                node_attrs = {}
                for key, value in node.items():
                    if key != 'id':
                        if isinstance(value, (list, dict)):
                            node_attrs[key] = json.dumps(value)
                        else:
                            node_attrs[key] = str(value) if value is not None else ''
                
                G.add_node(node['id'], **node_attrs)
            
            # Add edges with attributes
            for edge in self.edges:
                edge_attrs = {}
                for key, value in edge.items():
                    if key not in ['source', 'target']:
                        if isinstance(value, dict):
                            edge_attrs[key] = json.dumps(value)
                        else:
                            edge_attrs[key] = str(value) if value is not None else ''
                
                G.add_edge(edge['source'], edge['target'], **edge_attrs)
            
            # Export to GEXF
            nx.write_gexf(G, output_path)
            return True
        except Exception as e:
            print(f"Error exporting GEXF: {e}")
            return False
    
    def export_dot(self, output_path: str) -> bool:
        """Export as DOT format (Graphviz)"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("digraph KnowledgeGraph {\n")
                f.write("  rankdir=LR;\n")
                f.write("  node [shape=box, style=rounded];\n\n")
                
                # Write nodes
                for node in self.nodes:
                    node_id = node['id'].replace('-', '_')
                    title = node.get('title', 'Unknown').replace('"', '\\"')[:50]
                    level = node.get('level', 0)
                    content_type = node.get('content_type', 'unknown')
                    
                    # Color by level
                    colors = ['red', 'orange', 'blue', 'green', 'purple']
                    color = colors[level % len(colors)]
                    
                    f.write(f'  {node_id} [label="{title}\\n({content_type})", color={color}];\n')
                
                f.write("\n")
                
                # Write edges
                for edge in self.edges:
                    source_id = edge['source'].replace('-', '_')
                    target_id = edge['target'].replace('-', '_')
                    relationship = edge.get('relationship', 'related')
                    weight = edge.get('weight', 1.0)
                    
                    f.write(f'  {source_id} -> {target_id} [label="{relationship}", weight={weight}];\n')
                
                f.write("}\n")
            
            return True
        except Exception as e:
            print(f"Error exporting DOT: {e}")
            return False
    
    def export_cypher(self, output_path: str) -> bool:
        """Export as Cypher CREATE statements for Neo4j"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("// Knowledge Graph Export to Neo4j Cypher\n")
                f.write(f"// Generated on: {datetime.now().isoformat()}\n\n")
                
                # Clear existing data
                f.write("// Clear existing data\n")
                f.write("MATCH (n:KnowledgeNode) DETACH DELETE n;\n\n")
                
                # Create nodes
                f.write("// Create nodes\n")
                for node in self.nodes:
                    node_id = node['id']
                    properties = []
                    
                    for key, value in node.items():
                        if key == 'id':
                            continue
                        
                        if value is not None:
                            if isinstance(value, str):
                                # Escape quotes
                                escaped_value = value.replace("'", "\\'").replace('"', '\\"')
                                properties.append(f"{key}: '{escaped_value}'")
                            elif isinstance(value, (list, dict)):
                                json_value = json.dumps(value).replace("'", "\\'").replace('"', '\\"')
                                properties.append(f"{key}: '{json_value}'")
                            else:
                                properties.append(f"{key}: {value}")
                    
                    props_str = ', '.join(properties)
                    f.write(f"CREATE (n:KnowledgeNode {{id: '{node_id}', {props_str}}});\n")
                
                f.write("\n// Create relationships\n")
                
                # Create relationships
                for edge in self.edges:
                    source_id = edge['source']
                    target_id = edge['target']
                    rel_type = edge['relationship'].upper().replace(' ', '_').replace('-', '_')
                    weight = edge.get('weight', 1.0)
                    metadata = edge.get('metadata', {})
                    
                    metadata_str = json.dumps(metadata).replace("'", "\\'").replace('"', '\\"')
                    
                    f.write(f"""MATCH (a:KnowledgeNode {{id: '{source_id}'}}), (b:KnowledgeNode {{id: '{target_id}'}})
CREATE (a)-[:{rel_type} {{weight: {weight}, metadata: '{metadata_str}'}}]->(b);\n""")
                
                # Create indexes
                f.write("\n// Create indexes for performance\n")
                indexes = [
                    "CREATE INDEX node_id_index IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.id);",
                    "CREATE INDEX node_title_index IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.title);",
                    "CREATE INDEX node_level_index IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.level);",
                    "CREATE INDEX node_domain_index IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.domain);"
                ]
                
                for index in indexes:
                    f.write(f"{index}\n")
            
            return True
        except Exception as e:
            print(f"Error exporting Cypher: {e}")
            return False
    
    def export_rdf_turtle(self, output_path: str, base_uri: str = "http://example.org/kg/") -> bool:
        """Export as RDF Turtle format"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("@prefix kg: <http://example.org/kg/> .\n")
                f.write("@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n")
                f.write("@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n")
                f.write("@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n")
                
                # Export nodes
                for node in self.nodes:
                    node_uri = f"kg:{node['id'].replace('-', '_')}"
                    f.write(f"{node_uri} rdf:type kg:KnowledgeNode ;\n")
                    
                    for key, value in node.items():
                        if key == 'id':
                            continue
                        
                        if value is not None:
                            if isinstance(value, str):
                                f.write(f'    kg:{key} "{value}" ;\n')
                            elif isinstance(value, (int, float)):
                                f.write(f'    kg:{key} {value} ;\n')
                            elif isinstance(value, (list, dict)):
                                json_str = json.dumps(value)
                                f.write(f'    kg:{key} "{json_str}" ;\n')
                    
                    f.write(".\n\n")
                
                # Export relationships
                for edge in self.edges:
                    source_uri = f"kg:{edge['source'].replace('-', '_')}"
                    target_uri = f"kg:{edge['target'].replace('-', '_')}"
                    rel_prop = f"kg:{edge['relationship'].replace(' ', '_').replace('-', '_')}"
                    
                    f.write(f"{source_uri} {rel_prop} {target_uri} .\n")
            
            return True
        except Exception as e:
            print(f"Error exporting RDF Turtle: {e}")
            return False
    
    def export_summary_report(self, output_path: str) -> bool:
        """Export a comprehensive summary report"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# Knowledge Graph Summary Report\n\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Basic statistics
                f.write("## Basic Statistics\n\n")
                f.write(f"- **Total Nodes**: {len(self.nodes)}\n")
                f.write(f"- **Total Edges**: {len(self.edges)}\n")
                
                if self.metadata:
                    f.write(f"- **Max Depth**: {self.metadata.get('max_depth', 'Unknown')}\n")
                    
                    levels = self.metadata.get('levels', {})
                    if levels:
                        f.write(f"- **Levels**: {len(levels)}\n")
                        for level, count in sorted(levels.items()):
                            f.write(f"  - Level {level}: {count} nodes\n")
                
                # Content type distribution
                content_types = {}
                for node in self.nodes:
                    ct = node.get('content_type', 'unknown')
                    content_types[ct] = content_types.get(ct, 0) + 1
                
                if content_types:
                    f.write("\n## Content Type Distribution\n\n")
                    for ct, count in sorted(content_types.items(), key=lambda x: x[1], reverse=True):
                        f.write(f"- **{ct}**: {count} nodes\n")
                
                # Domain distribution
                domains = {}
                for node in self.nodes:
                    domain = node.get('domain', 'unknown')
                    if domain:
                        domains[domain] = domains.get(domain, 0) + 1
                
                if domains:
                    f.write("\n## Domain Distribution\n\n")
                    for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True)[:10]:
                        f.write(f"- **{domain}**: {count} nodes\n")
                
                # Relationship types
                rel_types = {}
                for edge in self.edges:
                    rt = edge.get('relationship', 'unknown')
                    rel_types[rt] = rel_types.get(rt, 0) + 1
                
                if rel_types:
                    f.write("\n## Relationship Types\n\n")
                    for rt, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True):
                        f.write(f"- **{rt}**: {count} relationships\n")
                
                # Sample nodes
                f.write("\n## Sample Nodes\n\n")
                for i, node in enumerate(self.nodes[:5]):
                    f.write(f"### Node {i+1}: {node.get('title', 'Unknown')}\n\n")
                    f.write(f"- **URL**: {node.get('url', 'N/A')}\n")
                    f.write(f"- **Level**: {node.get('level', 'N/A')}\n")
                    f.write(f"- **Content Type**: {node.get('content_type', 'N/A')}\n")
                    f.write(f"- **Domain**: {node.get('domain', 'N/A')}\n")
                    
                    if node.get('summary'):
                        f.write(f"- **Summary**: {node['summary'][:200]}...\n")
                    
                    f.write("\n")
            
            return True
        except Exception as e:
            print(f"Error exporting summary report: {e}")
            return False
    
    def export_all_formats(self, output_dir: str, base_filename: str) -> Dict[str, bool]:
        """
        Export graph in all available formats
        
        Args:
            output_dir: Output directory
            base_filename: Base filename (without extension)
            
        Returns:
            Dictionary with format names and success status
        """
        os.makedirs(output_dir, exist_ok=True)
        
        results = {}
        
        # JSON
        results['json'] = self.export_json(
            os.path.join(output_dir, f"{base_filename}.json")
        )
        
        # CSV
        results['csv_nodes'] = self.export_csv_nodes(
            os.path.join(output_dir, f"{base_filename}_nodes.csv")
        )
        results['csv_edges'] = self.export_csv_edges(
            os.path.join(output_dir, f"{base_filename}_edges.csv")
        )
        
        # Triples
        results['triples_tsv'] = self.export_triples_tsv(
            os.path.join(output_dir, f"{base_filename}_triples.tsv")
        )
        
        # GraphML (if NetworkX available)
        if NETWORKX_AVAILABLE:
            results['graphml'] = self.export_graphml(
                os.path.join(output_dir, f"{base_filename}.graphml")
            )
            results['gexf'] = self.export_gexf(
                os.path.join(output_dir, f"{base_filename}.gexf")
            )
        
        # DOT
        results['dot'] = self.export_dot(
            os.path.join(output_dir, f"{base_filename}.dot")
        )
        
        # Cypher
        results['cypher'] = self.export_cypher(
            os.path.join(output_dir, f"{base_filename}.cypher")
        )
        
        # RDF Turtle
        results['rdf_turtle'] = self.export_rdf_turtle(
            os.path.join(output_dir, f"{base_filename}.ttl")
        )
        
        # Summary report
        results['summary'] = self.export_summary_report(
            os.path.join(output_dir, f"{base_filename}_summary.md")
        )
        
        return results


def get_supported_formats() -> Dict[str, str]:
    """Get dictionary of supported export formats and their descriptions"""
    formats = {
        'json': 'JavaScript Object Notation - Standard web format',
        'csv': 'Comma Separated Values - Spreadsheet compatible',
        'tsv': 'Tab Separated Values - Triple format',
        'graphml': 'GraphML - XML-based graph format (requires NetworkX)',
        'gexf': 'GEXF - Graph Exchange XML Format (requires NetworkX)',
        'dot': 'DOT - Graphviz format for visualization',
        'cypher': 'Cypher - Neo4j database import format',
        'rdf_turtle': 'RDF Turtle - Semantic web format',
        'summary': 'Markdown summary report'
    }
    
    if not NETWORKX_AVAILABLE:
        formats['graphml'] += ' (NOT AVAILABLE - install networkx)'
        formats['gexf'] += ' (NOT AVAILABLE - install networkx)'
    
    return formats
