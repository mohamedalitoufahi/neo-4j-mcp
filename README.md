# Neo4j Agentic Chatbot with MCP Server

This is a **dockerized agentic chatbot** that uses **CrewAI** and **Neo4j** database to provide intelligent graph database interactions. The chatbot communicates with a Neo4j database through an **MCP** (Model Context Protocol) server, allowing natural language queries and operations on graph data.


## 🏗️ Architecture

```
┌─────────────────────┐    HTTP     ┌─────────────────────┐    Bolt/HTTP     ┌─────────────────┐
│                     │             │                     │                  │                 │
│   Graph Agent       │◄───────────►│   MCP Server        │◄────────────────►│   Neo4j DB      │
│   (CrewAI)          │             │   (FastMCP)         │                  │   (Database)    │
│                     │             │                     │                  │                 │
└─────────────────────┘             └─────────────────────┘                  └─────────────────┘
```


### Components

1. **Graph Agent (`graph_agent/`)** - An intelligent conversational agent powered by CrewAI and Google Gemini
2. **MCP Server (`mcp-server/`)** - A Model Context Protocol server that exposes Neo4j database operations
3. **Neo4j Database** - External graph database for data storage

## 🚀 Features

- **Natural Language Interface**: Chat with your Neo4j database using plain English
- **Intelligent Query Generation**: The agent translates requests into optimal Cypher queries
- **Graph Operations**: Create nodes, relationships, and perform complex graph analytics
- **Containerized Deployment**: Both components are fully dockerized
- **HTTP Communication**: Seamless communication between agent and database server


## 🛠️ Available Operations

- **Database Information**: Get schema, node counts, relationship types
- **Create Nodes**: Add new nodes with labels and properties
- **Find Nodes**: Search for nodes by label and properties
- **Execute Cypher**: Run custom Cypher queries for complex operations

##  Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Neo4j database running 
- Google Cloud credentials for Gemini LLM

### Setup Environment Variables
Create a `.env` file in the `mcp-server/` directory:

```bash
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USERNAME=your-username  
NEO4J_PASSWORD=your-password
```
Create a `.env` file in the `graph_agent directory:

```bash
GOOGLE_CLOUD_CREDENTIALS = path-to-your-google-cloud-credentials
```

1. **Clone the repository**
```bash
git clone https://github.com/mohamedalitoufahi/neo-4j-mcp.git
cd neo-4j-mcp
```

2. **Start the MCP Server**
```bash
cd mcp-server
docker compose up
```

3. **Start the Graph Agent**
```bash
cd ../graph_agent
docker compose up
```

## 📚 Technology Stack

- **CrewAI**: Multi-agent orchestration framework
- **FastMCP**: Model Context Protocol implementation  
- **Neo4j**: Graph database
- **Google Gemini**: Large language model
- **Docker**: Containerization platform

## 📄 License

This project is licensed under the MIT License.
