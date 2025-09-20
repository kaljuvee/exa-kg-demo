import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os
import sys
import math

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from utils.search_util import search, find_similar, get_contents
from utils.knowledge_graph import KnowledgeGraphBuilder, create_subject_predicate_object_triples

# Page configuration
st.set_page_config(
    page_title="Exa Knowledge Graph Explorer",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🕸️ Exa Knowledge Graph Explorer")
st.markdown("""
This application uses the Exa.ai API to build and visualize knowledge graphs from web content. 
Enter a company name or URL to explore connections and relationships in an interactive graph.
""")

# Sidebar configuration
st.sidebar.header("Configuration")

# Input method selection
input_method = st.sidebar.radio(
    "Input Method",
    ["Company Name", "URL"]
)

# Input field based on selection
if input_method == "Company Name":
    user_input = st.sidebar.text_input(
        "Enter Company Name",
        placeholder="e.g., OpenAI, Tesla, Microsoft"
    )
    search_query = f"{user_input} company information" if user_input else ""
else:
    user_input = st.sidebar.text_input(
        "Enter URL",
        placeholder="https://example.com"
    )
    search_query = user_input

# Graph depth configuration
graph_depth = st.sidebar.slider(
    "Graph Depth (n-levels)",
    min_value=1,
    max_value=5,
    value=2,
    help="Number of levels to explore in the knowledge graph"
)

# Number of results per level
results_per_level = st.sidebar.slider(
    "Results per Level",
    min_value=5,
    max_value=25,
    value=10,
    help="Number of results to fetch at each level"
)

# Search button
search_button = st.sidebar.button("🔍 Build Knowledge Graph", type="primary")

# Main content area
if search_button and user_input:
    with st.spinner("Building knowledge graph..."):
        # Initialize the knowledge graph builder
        kg_builder = KnowledgeGraphBuilder(
            max_depth=graph_depth,
            max_results_per_level=results_per_level
        )
        
        # Build the graph
        st.info(f"🔍 Building knowledge graph for: {search_query}")
        
        input_type = "search" if input_method == "Company Name" else "url"
        query = search_query if input_method == "Company Name" else user_input
        
        # Build the graph
        graph_data = kg_builder.build_graph(query, input_type)
        
        # Store in session state
        st.session_state.graph_data = graph_data
        
        # Display statistics
        stats = kg_builder.get_graph_statistics()
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Nodes", stats['node_count'])
            with col2:
                st.metric("Edges", stats['edge_count'])
            with col3:
                st.metric("Levels", stats['levels'])
            with col4:
                st.metric("Domains", stats['domains'])
            
            st.success(f"✅ Knowledge graph built successfully!")
        else:
            st.error("❌ Failed to build knowledge graph. Please try a different query.")

# Display graph if data exists
if 'graph_data' in st.session_state and st.session_state.graph_data['nodes']:
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Graph Visualization", "📋 Node Details", "🔗 Relationships", "💾 Export Data"])
    
    with tab1:
        st.subheader("Interactive Knowledge Graph")
        
        # Prepare data for Plotly network graph
        nodes = st.session_state.graph_data['nodes']
        edges = st.session_state.graph_data['edges']
        
        # Group nodes by level for positioning
        nodes_by_level = {}
        for node in nodes:
            level = node['level']
            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node)
        
        # Create node positions (circular layout by level)
        node_positions = {}
        
        for level, level_nodes in nodes_by_level.items():
            num_nodes = len(level_nodes)
            radius = 200 + level * 150
            
            for i, node in enumerate(level_nodes):
                angle = 2 * math.pi * i / max(num_nodes, 1)
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                node_positions[node['id']] = (x, y)
        
        # Create edge traces
        edge_x = []
        edge_y = []
        edge_info = []
        
        for edge in edges:
            source_pos = node_positions.get(edge['source'])
            target_pos = node_positions.get(edge['target'])
            
            if source_pos and target_pos:
                edge_x.extend([source_pos[0], target_pos[0], None])
                edge_y.extend([source_pos[1], target_pos[1], None])
                edge_info.append(f"Relationship: {edge['relationship']}")
        
        # Create node traces by type
        node_traces = {}
        color_map = {
            'root': 'red',
            'primary': 'orange', 
            'secondary': 'blue',
            'tertiary': 'green'
        }
        
        for node in nodes:
            node_type = node.get('node_type', 'secondary')
            if node_type not in node_traces:
                node_traces[node_type] = {
                    'x': [], 'y': [], 'text': [], 'hovertext': [],
                    'color': color_map.get(node_type, 'gray'),
                    'size': 20 if node_type == 'root' else 15
                }
            
            pos = node_positions.get(node['id'])
            if pos:
                node_traces[node_type]['x'].append(pos[0])
                node_traces[node_type]['y'].append(pos[1])
                node_traces[node_type]['text'].append(f"{node['title'][:30]}...")
                
                # Create hover text with details
                hover_text = f"<b>{node['title']}</b><br>"
                hover_text += f"Type: {node.get('content_type', 'Unknown')}<br>"
                hover_text += f"Level: {node['level']}<br>"
                hover_text += f"Domain: {node.get('domain', 'Unknown')}<br>"
                if node.get('author'):
                    hover_text += f"Author: {node['author']}<br>"
                if node.get('entities'):
                    hover_text += f"Entities: {', '.join(node['entities'][:3])}<br>"
                
                node_traces[node_type]['hovertext'].append(hover_text)
        
        # Create the plot
        fig = go.Figure()
        
        # Add edges
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='rgba(128,128,128,0.5)'),
            hoverinfo='none',
            mode='lines',
            name='Connections',
            showlegend=False
        ))
        
        # Add node traces
        for node_type, trace_data in node_traces.items():
            fig.add_trace(go.Scatter(
                x=trace_data['x'], 
                y=trace_data['y'],
                mode='markers',
                hoverinfo='text',
                hovertext=trace_data['hovertext'],
                marker=dict(
                    size=trace_data['size'],
                    color=trace_data['color'],
                    line=dict(width=2, color='white')
                ),
                name=f"{node_type.title()} Nodes"
            ))
        
        fig.update_layout(
            title="Knowledge Graph Visualization",
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=700,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Node Details")
        
        # Group nodes by level
        nodes_by_level = {}
        for node in st.session_state.graph_data['nodes']:
            level = node['level']
            if level not in nodes_by_level:
                nodes_by_level[level] = []
            nodes_by_level[level].append(node)
        
        # Display nodes by level
        for level in sorted(nodes_by_level.keys()):
            level_nodes = nodes_by_level[level]
            st.write(f"**Level {level}** ({len(level_nodes)} nodes)")
            
            for node in level_nodes:
                with st.expander(f"📄 {node['title'][:80]}..."):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**URL:** {node['url']}")
                        if node.get('summary'):
                            st.write(f"**Summary:** {node['summary']}")
                        if node.get('author'):
                            st.write(f"**Author:** {node['author']}")
                        if node.get('published_date'):
                            st.write(f"**Published:** {node['published_date']}")
                        if node.get('entities'):
                            st.write(f"**Entities:** {', '.join(node['entities'][:5])}")
                        if node.get('keywords'):
                            st.write(f"**Keywords:** {', '.join(node['keywords'][:5])}")
                    
                    with col2:
                        st.write(f"**Level:** {node['level']}")
                        st.write(f"**Type:** {node.get('node_type', 'Unknown')}")
                        st.write(f"**Content Type:** {node.get('content_type', 'Unknown')}")
                        st.write(f"**Domain:** {node.get('domain', 'Unknown')}")
    
    with tab3:
        st.subheader("Relationship Analysis")
        
        edges = st.session_state.graph_data['edges']
        nodes = {node['id']: node for node in st.session_state.graph_data['nodes']}
        
        # Relationship statistics
        relationship_counts = {}
        for edge in edges:
            rel_type = edge['relationship']
            relationship_counts[rel_type] = relationship_counts.get(rel_type, 0) + 1
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("**Relationship Types:**")
            for rel_type, count in sorted(relationship_counts.items()):
                st.write(f"• {rel_type}: {count}")
        
        with col2:
            # Create relationship type distribution chart
            if relationship_counts:
                fig_rel = px.pie(
                    values=list(relationship_counts.values()),
                    names=list(relationship_counts.keys()),
                    title="Relationship Distribution"
                )
                st.plotly_chart(fig_rel, use_container_width=True)
        
        # Subject-Predicate-Object Triples
        st.subheader("Knowledge Triples (Subject-Predicate-Object)")
        
        triples = create_subject_predicate_object_triples(st.session_state.graph_data)
        
        if triples:
            # Display first 20 triples in a table
            import pandas as pd
            
            triples_df = pd.DataFrame(triples[:20], columns=['Subject', 'Predicate', 'Object'])
            st.dataframe(triples_df, use_container_width=True)
            
            # Download all triples
            triples_text = "\n".join([f"{s} | {p} | {o}" for s, p, o in triples])
            st.download_button(
                label="📥 Download All Triples",
                data=triples_text,
                file_name=f"knowledge_triples_{user_input.replace(' ', '_')}.txt",
                mime="text/plain"
            )
        
        # Detailed edge information
        st.subheader("Detailed Relationships")
        
        for edge in edges[:10]:  # Show first 10 edges
            source_node = nodes.get(edge['source'])
            target_node = nodes.get(edge['target'])
            
            if source_node and target_node:
                with st.expander(f"{source_node['title'][:40]} → {target_node['title'][:40]}"):
                    st.write(f"**Relationship:** {edge['relationship']}")
                    st.write(f"**Weight:** {edge.get('weight', 'N/A')}")
                    if edge.get('metadata'):
                        st.write(f"**Metadata:** {edge['metadata']}")
    
    with tab4:
        st.subheader("Export Knowledge Graph Data")
        
        # Multiple export formats
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON export
            json_data = json.dumps(st.session_state.graph_data, indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name=f"knowledge_graph_{user_input.replace(' ', '_')}.json",
                mime="application/json"
            )
            
            # CSV export for nodes
            import pandas as pd
            nodes_df = pd.DataFrame(st.session_state.graph_data['nodes'])
            csv_nodes = nodes_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Nodes as CSV",
                data=csv_nodes,
                file_name=f"kg_nodes_{user_input.replace(' ', '_')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # CSV export for edges
            edges_df = pd.DataFrame(st.session_state.graph_data['edges'])
            csv_edges = edges_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Edges as CSV",
                data=csv_edges,
                file_name=f"kg_edges_{user_input.replace(' ', '_')}.csv",
                mime="text/csv"
            )
            
            # Triples export
            triples = create_subject_predicate_object_triples(st.session_state.graph_data)
            triples_text = "\n".join([f"{s}\t{p}\t{o}" for s, p, o in triples])
            st.download_button(
                label="📥 Download Triples (TSV)",
                data=triples_text,
                file_name=f"kg_triples_{user_input.replace(' ', '_')}.tsv",
                mime="text/tab-separated-values"
            )
        
        # Display metadata
        st.subheader("Graph Metadata")
        metadata = st.session_state.graph_data.get('metadata', {})
        if metadata:
            col1, col2 = st.columns(2)
            with col1:
                st.json(metadata)
            with col2:
                # Content type distribution
                content_types = metadata.get('content_types', {})
                if content_types:
                    fig_content = px.bar(
                        x=list(content_types.keys()),
                        y=list(content_types.values()),
                        title="Content Type Distribution"
                    )
                    st.plotly_chart(fig_content, use_container_width=True)
        
        # Display JSON preview
        with st.expander("Preview JSON Data"):
            st.json(st.session_state.graph_data)

else:
    # Welcome message
    st.info("👈 Use the sidebar to configure your search and build a knowledge graph!")
    
    # Example usage
    st.subheader("How to Use")
    st.markdown("""
    1. **Choose Input Method**: Select either "Company Name" or "URL"
    2. **Enter Your Query**: Type a company name (e.g., "OpenAI") or paste a URL
    3. **Configure Depth**: Set how many levels deep you want to explore (1-5)
    4. **Set Results**: Choose how many results to fetch per level (5-25)
    5. **Build Graph**: Click the search button to start building your knowledge graph
    6. **Explore**: View the interactive visualization, node details, and export data
    """)
    
    st.subheader("Features")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🔍 Smart Search**
        - Company-based queries
        - URL similarity search
        - Configurable depth
        """)
    
    with col2:
        st.markdown("""
        **📊 Visualization**
        - Interactive network graph
        - Level-based coloring
        - Hover details
        """)
    
    with col3:
        st.markdown("""
        **💾 Export Options**
        - JSON format
        - Complete graph data
        - Node relationships
        """)
