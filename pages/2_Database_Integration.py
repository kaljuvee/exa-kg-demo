import streamlit as st
import json
import os
import sys
from datetime import datetime

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from utils.neo4j_integration import Neo4jKnowledgeGraph, setup_local_neo4j, create_sample_queries
from utils.export_utils import KnowledgeGraphExporter, get_supported_formats

# Page configuration
st.set_page_config(
    page_title="Database Integration - Exa KG",
    page_icon="🗄️",
    layout="wide"
)

st.title("🗄️ Database Integration & Advanced Export")
st.markdown("""
This page provides advanced database integration with Neo4j and comprehensive export options 
for your knowledge graphs in multiple formats.
""")

# Check if graph data exists
if 'graph_data' not in st.session_state or not st.session_state.graph_data.get('nodes'):
    st.warning("⚠️ No knowledge graph data found. Please build a graph first using the main page.")
    st.stop()

# Create tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["🗄️ Neo4j Integration", "📤 Advanced Export", "📊 Database Queries"])

with tab1:
    st.header("Neo4j Database Integration")
    
    # Neo4j connection settings
    st.subheader("Connection Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        neo4j_uri = st.text_input("Neo4j URI", value="bolt://localhost:7687")
        neo4j_user = st.text_input("Username", value="neo4j")
        neo4j_password = st.text_input("Password", type="password", value="password")
    
    with col2:
        st.info("**Setup Instructions:**")
        st.markdown(setup_local_neo4j())
    
    # Connection and import section
    st.subheader("Database Operations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔌 Test Connection", type="primary"):
            with st.spinner("Testing connection..."):
                try:
                    neo4j_kg = Neo4jKnowledgeGraph(neo4j_uri, neo4j_user, neo4j_password)
                    if neo4j_kg.connect():
                        st.success("✅ Connection successful!")
                        st.session_state.neo4j_connected = True
                        st.session_state.neo4j_kg = neo4j_kg
                    else:
                        st.error("❌ Connection failed!")
                        st.session_state.neo4j_connected = False
                except Exception as e:
                    st.error(f"❌ Connection error: {e}")
                    st.session_state.neo4j_connected = False
    
    with col2:
        if st.button("📥 Import to Neo4j"):
            if st.session_state.get('neo4j_connected'):
                with st.spinner("Importing knowledge graph..."):
                    try:
                        neo4j_kg = st.session_state.neo4j_kg
                        success = neo4j_kg.import_knowledge_graph(st.session_state.graph_data)
                        if success:
                            st.success("✅ Graph imported successfully!")
                        else:
                            st.error("❌ Import failed!")
                    except Exception as e:
                        st.error(f"❌ Import error: {e}")
            else:
                st.warning("Please test connection first!")
    
    with col3:
        if st.button("🗑️ Clear Database"):
            if st.session_state.get('neo4j_connected'):
                if st.checkbox("I understand this will delete all data"):
                    with st.spinner("Clearing database..."):
                        try:
                            neo4j_kg = st.session_state.neo4j_kg
                            neo4j_kg.clear_database()
                            st.success("✅ Database cleared!")
                        except Exception as e:
                            st.error(f"❌ Clear error: {e}")
            else:
                st.warning("Please test connection first!")
    
    # Database statistics
    if st.session_state.get('neo4j_connected'):
        st.subheader("Database Statistics")
        
        if st.button("📊 Refresh Stats"):
            try:
                neo4j_kg = st.session_state.neo4j_kg
                stats = neo4j_kg.get_database_stats()
                
                if stats:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Nodes", stats.get('node_count', 0))
                    with col2:
                        st.metric("Relationships", stats.get('relationship_count', 0))
                    with col3:
                        rel_types = stats.get('relationship_types', {})
                        st.metric("Relationship Types", len(rel_types))
                    with col4:
                        level_dist = stats.get('level_distribution', {})
                        st.metric("Levels", len(level_dist))
                    
                    # Relationship distribution
                    if rel_types:
                        st.subheader("Relationship Distribution")
                        import plotly.express as px
                        fig = px.bar(
                            x=list(rel_types.keys()),
                            y=list(rel_types.values()),
                            title="Relationship Types in Database"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Level distribution
                    if level_dist:
                        st.subheader("Level Distribution")
                        fig = px.pie(
                            values=list(level_dist.values()),
                            names=[f"Level {k}" for k in level_dist.keys()],
                            title="Node Distribution by Level"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error getting stats: {e}")

with tab2:
    st.header("Advanced Export Options")
    
    # Initialize exporter
    exporter = KnowledgeGraphExporter(st.session_state.graph_data)
    
    # Export format selection
    st.subheader("Available Export Formats")
    
    formats = get_supported_formats()
    
    # Display format information
    for format_name, description in formats.items():
        st.write(f"**{format_name.upper()}**: {description}")
    
    st.subheader("Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Single format exports
        st.write("**Single Format Export:**")
        
        selected_format = st.selectbox(
            "Choose format",
            list(formats.keys()),
            format_func=lambda x: f"{x.upper()} - {formats[x].split(' - ')[0]}"
        )
        
        if st.button(f"📤 Export as {selected_format.upper()}"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"knowledge_graph_{timestamp}"
            
            success = False
            output_path = ""
            
            if selected_format == 'json':
                output_path = f"{filename}.json"
                success = exporter.export_json(output_path)
            elif selected_format == 'csv':
                # Export both nodes and edges
                nodes_path = f"{filename}_nodes.csv"
                edges_path = f"{filename}_edges.csv"
                success1 = exporter.export_csv_nodes(nodes_path)
                success2 = exporter.export_csv_edges(edges_path)
                success = success1 and success2
                if success:
                    with open(nodes_path, 'rb') as f:
                        st.download_button(
                            "📥 Download Nodes CSV",
                            f.read(),
                            file_name=f"kg_nodes_{timestamp}.csv",
                            mime="text/csv"
                        )
                    with open(edges_path, 'rb') as f:
                        st.download_button(
                            "📥 Download Edges CSV",
                            f.read(),
                            file_name=f"kg_edges_{timestamp}.csv",
                            mime="text/csv"
                        )
            elif selected_format == 'tsv':
                output_path = f"{filename}_triples.tsv"
                success = exporter.export_triples_tsv(output_path)
            elif selected_format == 'graphml':
                output_path = f"{filename}.graphml"
                success = exporter.export_graphml(output_path)
            elif selected_format == 'gexf':
                output_path = f"{filename}.gexf"
                success = exporter.export_gexf(output_path)
            elif selected_format == 'dot':
                output_path = f"{filename}.dot"
                success = exporter.export_dot(output_path)
            elif selected_format == 'cypher':
                output_path = f"{filename}.cypher"
                success = exporter.export_cypher(output_path)
            elif selected_format == 'rdf_turtle':
                output_path = f"{filename}.ttl"
                success = exporter.export_rdf_turtle(output_path)
            elif selected_format == 'summary':
                output_path = f"{filename}_summary.md"
                success = exporter.export_summary_report(output_path)
            
            if success and output_path and os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    st.download_button(
                        f"📥 Download {selected_format.upper()}",
                        f.read(),
                        file_name=os.path.basename(output_path),
                        mime="application/octet-stream"
                    )
                st.success(f"✅ {selected_format.upper()} export successful!")
            elif success:
                st.success(f"✅ {selected_format.upper()} export successful!")
            else:
                st.error(f"❌ {selected_format.upper()} export failed!")
    
    with col2:
        # Bulk export
        st.write("**Bulk Export (All Formats):**")
        
        if st.button("📦 Export All Formats"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"knowledge_graph_{timestamp}"
            output_dir = "exports"
            
            with st.spinner("Exporting all formats..."):
                results = exporter.export_all_formats(output_dir, base_filename)
                
                # Display results
                successful = sum(1 for success in results.values() if success)
                total = len(results)
                
                st.write(f"**Export Results: {successful}/{total} successful**")
                
                for format_name, success in results.items():
                    if success:
                        st.success(f"✅ {format_name}")
                    else:
                        st.error(f"❌ {format_name}")
                
                # Create download links for successful exports
                if successful > 0:
                    st.write("**Download Files:**")
                    
                    for format_name, success in results.items():
                        if success:
                            # Determine file extension
                            extensions = {
                                'json': '.json',
                                'csv_nodes': '_nodes.csv',
                                'csv_edges': '_edges.csv',
                                'triples_tsv': '_triples.tsv',
                                'graphml': '.graphml',
                                'gexf': '.gexf',
                                'dot': '.dot',
                                'cypher': '.cypher',
                                'rdf_turtle': '.ttl',
                                'summary': '_summary.md'
                            }
                            
                            ext = extensions.get(format_name, '.txt')
                            file_path = os.path.join(output_dir, f"{base_filename}{ext}")
                            
                            if os.path.exists(file_path):
                                with open(file_path, 'rb') as f:
                                    st.download_button(
                                        f"📥 {format_name}",
                                        f.read(),
                                        file_name=os.path.basename(file_path),
                                        mime="application/octet-stream",
                                        key=f"download_{format_name}"
                                    )
    
    # Export preview
    st.subheader("Export Preview")
    
    preview_format = st.selectbox(
        "Preview format",
        ['json', 'cypher', 'dot', 'summary'],
        key="preview_format"
    )
    
    if st.button("👁️ Generate Preview"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        preview_file = f"preview_{timestamp}"
        
        if preview_format == 'json':
            preview_file += '.json'
            if exporter.export_json(preview_file):
                with open(preview_file, 'r') as f:
                    content = f.read()
                st.code(content[:2000] + "..." if len(content) > 2000 else content, language='json')
        elif preview_format == 'cypher':
            preview_file += '.cypher'
            if exporter.export_cypher(preview_file):
                with open(preview_file, 'r') as f:
                    content = f.read()
                st.code(content[:2000] + "..." if len(content) > 2000 else content, language='sql')
        elif preview_format == 'dot':
            preview_file += '.dot'
            if exporter.export_dot(preview_file):
                with open(preview_file, 'r') as f:
                    content = f.read()
                st.code(content, language='text')
        elif preview_format == 'summary':
            preview_file += '_summary.md'
            if exporter.export_summary_report(preview_file):
                with open(preview_file, 'r') as f:
                    content = f.read()
                st.markdown(content)

with tab3:
    st.header("Database Queries")
    
    if not st.session_state.get('neo4j_connected'):
        st.warning("⚠️ Please connect to Neo4j database first to run queries.")
    else:
        st.subheader("Sample Queries")
        
        # Get sample queries
        sample_queries = create_sample_queries()
        
        # Query selector
        selected_query_name = st.selectbox(
            "Choose a sample query",
            list(sample_queries.keys())
        )
        
        selected_query = sample_queries[selected_query_name]
        
        # Query editor
        st.subheader("Query Editor")
        query_text = st.text_area(
            "Cypher Query",
            value=selected_query,
            height=150
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ Run Query"):
                if query_text.strip():
                    try:
                        neo4j_kg = st.session_state.neo4j_kg
                        
                        with neo4j_kg.driver.session() as session:
                            result = session.run(query_text)
                            records = list(result)
                            
                            if records:
                                st.success(f"✅ Query executed successfully! Found {len(records)} results.")
                                
                                # Display results
                                if len(records) > 0:
                                    # Convert to displayable format
                                    display_data = []
                                    for record in records[:50]:  # Limit to first 50 results
                                        row_data = {}
                                        for key in record.keys():
                                            value = record[key]
                                            if hasattr(value, '__dict__'):
                                                # Neo4j node or relationship
                                                row_data[key] = str(dict(value))
                                            else:
                                                row_data[key] = str(value)
                                        display_data.append(row_data)
                                    
                                    # Display as dataframe
                                    import pandas as pd
                                    df = pd.DataFrame(display_data)
                                    st.dataframe(df, use_container_width=True)
                                    
                                    if len(records) > 50:
                                        st.info(f"Showing first 50 of {len(records)} results.")
                            else:
                                st.info("Query executed successfully but returned no results.")
                                
                    except Exception as e:
                        st.error(f"❌ Query error: {e}")
                else:
                    st.warning("Please enter a query.")
        
        with col2:
            if st.button("📋 Copy Query"):
                st.code(query_text, language='sql')
        
        # Quick actions
        st.subheader("Quick Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Get Node Count"):
                try:
                    neo4j_kg = st.session_state.neo4j_kg
                    with neo4j_kg.driver.session() as session:
                        result = session.run("MATCH (n:KnowledgeNode) RETURN count(n) as count")
                        count = result.single()['count']
                        st.metric("Total Nodes", count)
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col2:
            if st.button("🔗 Get Relationship Count"):
                try:
                    neo4j_kg = st.session_state.neo4j_kg
                    with neo4j_kg.driver.session() as session:
                        result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                        count = result.single()['count']
                        st.metric("Total Relationships", count)
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col3:
            if st.button("🏆 Most Connected Node"):
                try:
                    neo4j_kg = st.session_state.neo4j_kg
                    with neo4j_kg.driver.session() as session:
                        result = session.run("""
                            MATCH (n:KnowledgeNode)
                            OPTIONAL MATCH (n)-[r]-()
                            WITH n, count(r) as connections
                            ORDER BY connections DESC
                            LIMIT 1
                            RETURN n.title as title, connections
                        """)
                        record = result.single()
                        if record:
                            st.metric("Most Connected", record['title'][:30] + "...", record['connections'])
                except Exception as e:
                    st.error(f"Error: {e}")

# Cleanup function
def cleanup_temp_files():
    """Clean up temporary files"""
    import glob
    temp_files = glob.glob("preview_*") + glob.glob("knowledge_graph_*")
    for file in temp_files:
        try:
            os.remove(file)
        except:
            pass

# Clean up on page load
cleanup_temp_files()
