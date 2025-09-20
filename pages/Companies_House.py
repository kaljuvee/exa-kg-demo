"""
Companies House Knowledge Graph Page

This page allows users to build knowledge graphs using UK Companies House data,
focusing on company relationships, directors, and ultimate beneficial owners.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import sys
import os
from datetime import datetime

# Add the utils directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

try:
    from companies_house_api import CompaniesHouseAPI, CompanyProfile, Officer, PSC
except ImportError:
    st.error("Could not import Companies House API module. Please check the installation.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Companies House Knowledge Graph",
    page_icon="🏢",
    layout="wide"
)

def init_session_state():
    """Initialize session state variables"""
    if 'ch_graph_data' not in st.session_state:
        st.session_state.ch_graph_data = None
    if 'ch_api_key' not in st.session_state:
        st.session_state.ch_api_key = ""

def create_network_visualization(graph_data):
    """Create an interactive network visualization using Plotly"""
    if not graph_data or not graph_data['nodes']:
        return None
    
    # Extract node positions using a simple layout
    import math
    nodes = graph_data['nodes']
    edges = graph_data['edges']
    
    # Simple circular layout for nodes
    n_nodes = len(nodes)
    node_positions = {}
    
    for i, node in enumerate(nodes):
        angle = 2 * math.pi * i / n_nodes
        radius = 100 if node['type'] == 'Company' else 80
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
            edge_info.append(f"{edge['relationship']}: {edge.get('role', '')}")
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='#888'),
        hoverinfo='none',
        mode='lines'
    )
    
    # Create node traces by type
    node_traces = []
    
    for node_type in ['Company', 'Person', 'PSC']:
        type_nodes = [n for n in nodes if n['type'] == node_type]
        if not type_nodes:
            continue
        
        node_x = [node_positions[n['id']][0] for n in type_nodes]
        node_y = [node_positions[n['id']][1] for n in type_nodes]
        
        # Create hover text
        hover_text = []
        for node in type_nodes:
            if node['type'] == 'Company':
                text = f"<b>{node['label']}</b><br>"
                text += f"Number: {node.get('company_number', 'N/A')}<br>"
                text += f"Status: {node.get('status', 'N/A')}<br>"
                text += f"Business: {node.get('business_activity', 'N/A')}"
            elif node['type'] == 'Person':
                text = f"<b>{node['label']}</b><br>"
                text += f"Role: {node.get('role', 'N/A')}<br>"
                text += f"Nationality: {node.get('nationality', 'N/A')}<br>"
                text += f"Occupation: {node.get('occupation', 'N/A')}"
            else:  # PSC
                text = f"<b>{node['label']}</b><br>"
                text += f"Type: {node.get('psc_type', 'N/A')}<br>"
                text += f"Country: {node.get('country_of_residence', 'N/A')}"
            hover_text.append(text)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            hovertext=hover_text,
            text=[n['label'] for n in type_nodes],
            textposition="middle center",
            name=node_type,
            marker=dict(
                size=[n.get('size', 15) for n in type_nodes],
                color=type_nodes[0]['color'],
                line=dict(width=2, color='white')
            )
        )
        node_traces.append(node_trace)
    
    # Create the figure
    fig = go.Figure(data=[edge_trace] + node_traces,
                    layout=go.Layout(
                        title=dict(
                            text="Companies House Knowledge Graph",
                            font=dict(size=16)
                        ),
                        showlegend=True,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        annotations=[ dict(
                            text="Hover over nodes for details",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002,
                            xanchor="left", yanchor="bottom",
                            font=dict(color="#888", size=12)
                        )],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        plot_bgcolor='white'
                    ))
    
    return fig

def display_company_details(graph_data):
    """Display detailed information about companies in the graph"""
    if not graph_data or not graph_data['nodes']:
        st.write("No company data available.")
        return
    
    companies = [n for n in graph_data['nodes'] if n['type'] == 'Company']
    
    for company in companies:
        with st.expander(f"🏢 {company['label']} ({company.get('company_number', 'N/A')})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Status:** {company.get('status', 'N/A')}")
                st.write(f"**Incorporation Date:** {company.get('incorporation_date', 'N/A')}")
                st.write(f"**Business Activity:** {company.get('business_activity', 'N/A')}")
            
            with col2:
                sic_codes = company.get('sic_codes', [])
                if sic_codes:
                    st.write(f"**SIC Codes:** {', '.join(sic_codes)}")
                else:
                    st.write("**SIC Codes:** N/A")

def display_people_network(graph_data):
    """Display information about people in the network"""
    if not graph_data or not graph_data['nodes']:
        st.write("No people data available.")
        return
    
    people = [n for n in graph_data['nodes'] if n['type'] in ['Person', 'PSC']]
    
    if not people:
        st.write("No people found in the network.")
        return
    
    # Create a DataFrame for better display
    people_data = []
    for person in people:
        people_data.append({
            'Name': person['label'],
            'Type': person['type'],
            'Role/Control': person.get('role') or person.get('psc_type', 'N/A'),
            'Nationality': person.get('nationality', 'N/A'),
            'Country of Residence': person.get('country_of_residence', 'N/A')
        })
    
    df = pd.DataFrame(people_data)
    st.dataframe(df, use_container_width=True)

def display_relationships(graph_data):
    """Display relationship information"""
    if not graph_data or not graph_data['edges']:
        st.write("No relationships available.")
        return
    
    # Create a DataFrame for relationships
    relationships_data = []
    for edge in graph_data['edges']:
        # Find source and target labels
        source_node = next((n for n in graph_data['nodes'] if n['id'] == edge['source']), None)
        target_node = next((n for n in graph_data['nodes'] if n['id'] == edge['target']), None)
        
        if source_node and target_node:
            relationships_data.append({
                'From': source_node['label'],
                'Relationship': edge['relationship'],
                'To': target_node['label'],
                'Details': edge.get('role') or ', '.join(edge.get('nature_of_control', [])) or 'N/A',
                'Date': edge.get('appointed_on') or edge.get('notified_on', 'N/A')
            })
    
    df = pd.DataFrame(relationships_data)
    st.dataframe(df, use_container_width=True)

def export_companies_house_data(graph_data, format_type):
    """Export graph data in various formats"""
    if not graph_data:
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format_type == "JSON":
        filename = f"companies_house_graph_{timestamp}.json"
        data = json.dumps(graph_data, indent=2)
        return data, filename
    
    elif format_type == "CSV - Companies":
        companies = [n for n in graph_data['nodes'] if n['type'] == 'Company']
        df = pd.DataFrame(companies)
        filename = f"companies_house_companies_{timestamp}.csv"
        return df.to_csv(index=False), filename
    
    elif format_type == "CSV - People":
        people = [n for n in graph_data['nodes'] if n['type'] in ['Person', 'PSC']]
        df = pd.DataFrame(people)
        filename = f"companies_house_people_{timestamp}.csv"
        return df.to_csv(index=False), filename
    
    elif format_type == "CSV - Relationships":
        df = pd.DataFrame(graph_data['edges'])
        filename = f"companies_house_relationships_{timestamp}.csv"
        return df.to_csv(index=False), filename
    
    return None, None

def main():
    """Main function for the Companies House page"""
    init_session_state()
    
    st.title("🏢 Companies House Knowledge Graph Explorer")
    st.markdown("""
    Build knowledge graphs using official UK Companies House data. Explore company relationships, 
    directors, and ultimate beneficial owners (UBOs) through the Persons with Significant Control (PSC) register.
    """)
    
    # Sidebar configuration
    st.sidebar.header("🔧 Configuration")
    
    # API Key input
    api_key = st.sidebar.text_input(
        "Companies House API Key",
        type="password",
        value=st.session_state.ch_api_key,
        help="Get your free API key from https://developer.company-information.service.gov.uk/"
    )
    
    if api_key:
        st.session_state.ch_api_key = api_key
    
    # Input for company name or number
    company_input = st.sidebar.text_input(
        "Company Name or Number",
        placeholder="e.g., Tesco PLC, BP PLC, Vodafone, or 71431144",
        help="Enter a UK company name to search for, or a company number for direct access (useful for sandbox testing)"
    )
    
    max_companies = st.sidebar.slider(
        "Maximum Companies",
        min_value=1,
        max_value=20,
        value=5,
        help="Maximum number of companies to include in the graph"
    )
    
    # Build graph button
    if st.sidebar.button("🔍 Build Companies House Graph", type="primary"):
        if not api_key:
            st.sidebar.error("Please enter your Companies House API key")
        elif not company_input:
            st.sidebar.error("Please enter a company name")
        else:
            with st.spinner("Building knowledge graph from Companies House data..."):
                try:
                    # Initialize API client
                    ch_api = CompaniesHouseAPI(api_key, use_sandbox=False)
                    
                    # Build the network
                    graph_data = ch_api.get_company_network(company_input, max_companies)
                    
                    if graph_data and graph_data['nodes']:
                        st.session_state.ch_graph_data = graph_data
                        st.sidebar.success("✅ Knowledge graph built successfully!")
                    else:
                        st.sidebar.error("No companies found or API error occurred")
                        
                except Exception as e:
                    st.sidebar.error(f"Error: {str(e)}")
    
    # Display results if graph data exists
    if st.session_state.ch_graph_data:
        graph_data = st.session_state.ch_graph_data
        
        # Display summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            companies_count = len([n for n in graph_data['nodes'] if n['type'] == 'Company'])
            st.metric("Companies", companies_count)
        
        with col2:
            people_count = len([n for n in graph_data['nodes'] if n['type'] == 'Person'])
            st.metric("Directors/Officers", people_count)
        
        with col3:
            psc_count = len([n for n in graph_data['nodes'] if n['type'] == 'PSC'])
            st.metric("PSCs/UBOs", psc_count)
        
        with col4:
            relationships_count = len(graph_data['edges'])
            st.metric("Relationships", relationships_count)
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Graph Visualization", 
            "🏢 Company Details", 
            "👥 People Network", 
            "🔗 Relationships",
            "💾 Export Data"
        ])
        
        with tab1:
            st.subheader("Interactive Knowledge Graph")
            fig = create_network_visualization(graph_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("Unable to create visualization.")
        
        with tab2:
            st.subheader("Company Information")
            display_company_details(graph_data)
        
        with tab3:
            st.subheader("People in the Network")
            display_people_network(graph_data)
        
        with tab4:
            st.subheader("Relationships and Connections")
            display_relationships(graph_data)
        
        with tab5:
            st.subheader("Export Graph Data")
            
            col1, col2 = st.columns(2)
            
            with col1:
                export_format = st.selectbox(
                    "Export Format",
                    ["JSON", "CSV - Companies", "CSV - People", "CSV - Relationships"]
                )
            
            with col2:
                if st.button("📥 Download"):
                    data, filename = export_companies_house_data(graph_data, export_format)
                    if data and filename:
                        st.download_button(
                            label=f"Download {export_format}",
                            data=data,
                            file_name=filename,
                            mime="application/json" if export_format == "JSON" else "text/csv"
                        )
            
            # Display metadata
            st.subheader("Graph Metadata")
            metadata = graph_data.get('metadata', {})
            st.json(metadata)
    
    else:
        # Show instructions when no data is loaded
        st.info("👈 Use the sidebar to configure your search and build a Companies House knowledge graph!")
        
        # Show help information
        with st.expander("ℹ️ How to Get Started"):
            st.markdown("""
            ### Getting Your API Key
            
            1. **Register**: Go to [Companies House Developer Hub](https://developer.company-information.service.gov.uk/)
            2. **Create Account**: Sign up for a free developer account
            3. **Create Application**: Create a new application for your knowledge graph explorer
            4. **Generate API Key**: Create an API key for your application
            5. **Copy Key**: Copy the API key and paste it in the sidebar
            
            ### What You Can Explore
            
            - **Company Profiles**: Official company information, status, and business activities
            - **Directors & Officers**: Current and former company directors and secretaries
            - **Ultimate Beneficial Owners**: Persons with Significant Control (PSCs) who own or control companies
            - **Corporate Networks**: Relationships between companies through shared directors and ownership
            - **Business Activities**: SIC codes and business descriptions
            
            ### Example Companies to Try
            
            - **Tesco PLC** - Major UK retailer
            - **BP PLC** - Oil and gas company
            - **Vodafone Group PLC** - Telecommunications
            - **HSBC Holdings PLC** - Banking
            - **Rolls-Royce Holdings PLC** - Engineering
            """)

if __name__ == "__main__":
    main()
