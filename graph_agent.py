import asyncio
import json
import os
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# Google Gemini LLM configuration (same as your crew.py)
file_path = r"C:\Users\LENOVO\My Folders\MCP Server\formulai-dc0eba0c6712.json"

try:
    # Load the JSON credentials file
    with open(file_path, 'r') as file:
        vertex_credentials = json.load(file)
    
    # Convert the credentials to a JSON string
    vertex_credentials_json = json.dumps(vertex_credentials)
    
    # Create LLM instance with Gemini
    llm = LLM(
        model="gemini-2.5-flash",
        temperature=0.7,
        vertex_credentials=vertex_credentials_json
    )
    print("✅ Google Gemini LLM configured successfully!")
    
except FileNotFoundError:
    print(f"❌ Credentials file not found: {file_path}")
    print("Please make sure the Google credentials file exists.")
    exit(1)
except Exception as e:
    print(f"❌ Error configuring Gemini LLM: {e}")
    exit(1)


class Neo4jQueryInput(BaseModel):
    """Input schema for Neo4j query tool"""
    query: str = Field(..., description="Cypher query to execute")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Query parameters")


class CreateNodeInput(BaseModel):
    """Input schema for creating nodes"""
    label: str = Field(..., description="Node label (e.g., Person, Company)")
    properties: Dict[str, Any] = Field(..., description="Node properties as key-value pairs")


class FindNodesInput(BaseModel):
    """Input schema for finding nodes"""
    label: Optional[str] = Field(default=None, description="Node label to filter by")
    properties: Optional[Dict[str, Any]] = Field(default=None, description="Properties to match")
    limit: int = Field(default=10, description="Maximum number of nodes to return")


class Neo4jMCPTool(BaseTool):
    """Base class for Neo4j MCP tools"""
    server_url: str = "http://localhost:8051/mcp"
    
    async def _execute_mcp_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP tool call"""
        try:
            async with streamablehttp_client(self.server_url) as (read_stream, write_stream, get_session_id):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=arguments)
                    return json.loads(result.content[0].text)
        except Exception as e:
            return {"success": False, "error": str(e)}


class CypherQueryTool(Neo4jMCPTool):
    name: str = "cypher_query"
    description: str = "Execute Cypher queries against the Neo4j database. Use this for complex graph operations, analytics, and custom queries."
    args_schema: type[BaseModel] = Neo4jQueryInput

    def _run(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """Run Cypher query"""
        result = asyncio.run(self._execute_mcp_call("run_cypher_query", {
            "query": query, 
            "parameters": parameters or {}
        }))
        
        if result.get("success"):
            return f"Query executed successfully. Found {result.get('count', 0)} records.\nResults: {json.dumps(result.get('records', []), indent=2)}"
        else:
            return f"Query failed: {result.get('error', 'Unknown error')}"


class CreateNodeTool(Neo4jMCPTool):
    name: str = "create_node"
    description: str = "Create a new node in the Neo4j database with specified label and properties."
    args_schema: type[BaseModel] = CreateNodeInput

    def _run(self, label: str, properties: Dict[str, Any]) -> str:
        """Create a node"""
        result = asyncio.run(self._execute_mcp_call("create_node", {
            "label": label,
            "properties": properties
        }))
        
        if result.get("success"):
            node_id = result.get("id")
            return f"Successfully created {label} node with ID {node_id} and properties: {json.dumps(properties)}"
        else:
            return f"Failed to create node: {result.get('error', 'Unknown error')}"


class FindNodesTool(Neo4jMCPTool):
    name: str = "find_nodes"
    description: str = "Find nodes in the Neo4j database by label and/or properties."
    args_schema: type[BaseModel] = FindNodesInput

    def _run(self, label: Optional[str] = None, properties: Optional[Dict[str, Any]] = None, limit: int = 10) -> str:
        """Find nodes"""
        result = asyncio.run(self._execute_mcp_call("find_nodes", {
            "label": label,
            "properties": properties,
            "limit": limit
        }))
        
        if result.get("success"):
            nodes = result.get("nodes", [])
            return f"Found {len(nodes)} nodes:\n{json.dumps(nodes, indent=2)}"
        else:
            return f"Search failed: {result.get('error', 'Unknown error')}"


class DatabaseInfoTool(Neo4jMCPTool):
    name: str = "database_info"
    description: str = "Get comprehensive information about the Neo4j database including labels, relationships, and counts."
    
    def _run(self) -> str:
        """Get database info"""
        result = asyncio.run(self._execute_mcp_call("get_database_info", {}))
        
        if result.get("success"):
            info = {
                "node_labels": result.get("node_labels", []),
                "relationship_types": result.get("relationship_types", []),
                "node_count": result.get("node_count", 0),
                "relationship_count": result.get("relationship_count", 0)
            }
            return f"Database Overview:\n{json.dumps(info, indent=2)}"
        else:
            return f"Failed to get database info: {result.get('error', 'Unknown error')}"


def create_neo4j_agent() -> Agent:
    """Create a Neo4j Graph Database Agent"""
    return Agent(
        role="Graph Database Specialist",
        goal="Manage and analyze data in Neo4j graph databases using natural language commands",
        backstory="""You are an expert graph database administrator and analyst specializing in Neo4j. 
        You understand graph theory, Cypher query language, and can translate business requirements into 
        efficient graph operations. You excel at creating relationships between entities, analyzing 
        graph patterns, and providing insights from connected data.
        
        You can:
        - Create nodes and relationships 
        - Execute complex Cypher queries
        - Analyze graph structures and patterns
        - Provide recommendations for graph modeling
        - Help with data import and export
        - Optimize graph database performance
        
        Always explain your actions and provide clear, actionable insights.""",
        verbose=True,
        allow_delegation=False,
        llm=llm,  # Use the configured LLM
        tools=[
            CypherQueryTool(),
            CreateNodeTool(), 
            FindNodesTool(),
            DatabaseInfoTool()
        ]
    )


def interactive_cli():
    """Interactive CLI for the Neo4j agent"""
    agent = create_neo4j_agent()
    
    print("🚀 Neo4j Graph Database Assistant")
    print("=" * 50)
    print("I can help you manage your Neo4j database!")
    print("Try commands like:")
    print("- 'Show me database info'")
    print("- 'Create a Person node with name John and age 30'")
    print("- 'Find all Person nodes'")
    print("- 'Create a relationship between John and Jane as FRIENDS'")
    print("- 'Show me all nodes connected to John'")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
                
            if not user_input:
                continue
            
            # Create a task for the agent
            task = Task(
                description=f"Handle this request: {user_input}",
                agent=agent,
                expected_output="A clear response with the results of the database operation"
            )
            
            # Create a crew and execute
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=False
            )
            
            print("🤔 Processing...")
            result = crew.kickoff()
            print(f"🤖 Agent: {result.raw}")
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("Starting Neo4j Graph Database Assistant...")
    print("Make sure your Neo4j MCP server is running on http://localhost:8051")
    print("")
    
    # Test connection first
    try:
        tool = DatabaseInfoTool()
        result = tool._run()
        print("✅ Connection to Neo4j MCP server successful!")
        print("")
        interactive_cli()
    except Exception as e:
        print(f"❌ Failed to connect to Neo4j MCP server: {e}")
        print("Please make sure the server is running with: docker-compose up")
