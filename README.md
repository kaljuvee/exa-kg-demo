'''# Exa Knowledge Graph Explorer

This Streamlit application leverages the Exa.ai API to build and visualize knowledge graphs from web content. Users can input a company name or a URL to generate an n-level deep graph, exploring connections and relationships in an interactive visualization.

## Features

- **Dual Input Modes**: Start building a graph from either a company name or a specific URL.
- **Configurable Graph Depth**: Control the depth of the knowledge graph exploration (from 1 to 5 levels).
- **Interactive Visualization**: Explore the graph using an interactive Plotly visualization, with nodes colored by their level in the graph.
- **Detailed Node Information**: View detailed information for each node, including its URL, summary, author, and more.
- **Relationship Analysis**: Analyze the relationships between nodes, with a breakdown of relationship types.
- **Multiple Export Formats**: Export the entire knowledge graph, or parts of it, in various formats, including:
    - JSON (for the complete graph data)
    - CSV (for nodes and edges separately)
    - TSV (for subject-predicate-object triples)
    - GraphML and GEXF (for use in other graph analysis tools)
    - DOT (for Graphviz)
    - Cypher (for importing into a Neo4j database)
- **Neo4j Integration**: Connect to a local Neo4j database to import and query the knowledge graph.

## Project Structure

```
exa-kg-demo/
├── data/                 # Directory for exported data
├── docs/                 # Documentation files
├── pages/                # Additional Streamlit pages
│   └── Database_Integration.py
├── tests/                # Unit tests
│   ├── __init__.py
│   ├── test_knowledge_graph.py
│   └── test_search_util.py
├── utils/                # Utility modules
│   ├── __init__.py
│   ├── export_utils.py
│   ├── knowledge_graph.py
│   ├── neo4j_integration.py
│   └── search_util.py
├── Home.py               # Main Streamlit application file
└── README.md             # This file
```

## Setup and Installation

1.  **Clone the repository**:

    ```bash
    git clone https://github.com/kaljuvee/exa-kg-demo.git
    cd exa-kg-demo
    ```

2.  **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up your Exa API key**:

    Create a `.env` file in the root of the project and add your Exa API key:

    ```
    EXA_API_KEY="your-exa-api-key"
    ```

4.  **Run the Streamlit application**:

    ```bash
    streamlit run Home.py
    ```

## How to Use

1.  **Configure Your Search**: Use the sidebar to select your input method (Company Name or URL), enter your query, and configure the graph depth and results per level.
2.  **Build the Graph**: Click the "Build Knowledge Graph" button to start the process.
3.  **Explore the Visualization**: Interact with the graph in the "Graph Visualization" tab.
4.  **View Details**: See detailed information about each node and relationship in the "Node Details" and "Relationships" tabs.
5.  **Export Data**: Download the graph data in your preferred format from the "Export Data" tab.
6.  **Use Neo4j**: Navigate to the "Database Integration" page to connect to a Neo4j database, import the graph, and run queries.

## Testing

To run the unit tests, use the following command:

```bash
python -m unittest discover tests
```
'''
