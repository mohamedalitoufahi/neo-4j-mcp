from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase
from typing import Optional, List, Dict, Any
import json

load_dotenv("../env")

# Neo4j connection details
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Create an MCP server
mcp = FastMCP(
    name="Neo4j Database Server",
    host="0.0.0.0",
    port=8051,  # Different port from the calculator server
    stateless_http=True,
)

# Neo4j driver instance
driver = None

def get_neo4j_driver():
    """Get or create Neo4j driver instance"""
    global driver
    if driver is None:
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
    return driver

def close_driver():
    """Close the Neo4j driver"""
    global driver
    if driver:
        driver.close()
        driver = None

@mcp.tool()
def run_cypher_query(query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute a Cypher query against the Neo4j database.
    
    Args:
        query: The Cypher query to execute
        parameters: Optional parameters for the query
    
    Returns:
        Dictionary containing query results and metadata
    """
    if parameters is None:
        parameters = {}
    
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            result = session.run(query, parameters)
            
            # Convert result to a serializable format
            records = []
            for record in result:
                # Convert record to dictionary
                record_dict = {}
                for key in record.keys():
                    value = record[key]
                    # Handle Neo4j types that aren't JSON serializable
                    if hasattr(value, '__dict__'):
                        # For nodes and relationships, convert to dict
                        record_dict[key] = dict(value)
                    else:
                        record_dict[key] = value
                records.append(record_dict)
            
            return {
                "success": True,
                "records": records,
                "count": len(records),
                "query": query
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }

@mcp.tool()
def get_database_info() -> Dict[str, Any]:
    """
    Get basic information about the Neo4j database.
    
    Returns:
        Dictionary containing database metadata
    """
    try:
        driver = get_neo4j_driver()
        
        with driver.session() as session:
            # Get database info
            result = session.run("CALL db.info()")
            db_info = result.single()
            
            # Get node labels
            labels_result = session.run("CALL db.labels()")
            labels = [record["label"] for record in labels_result]
            
            # Get relationship types
            rel_types_result = session.run("CALL db.relationshipTypes()")
            rel_types = [record["relationshipType"] for record in rel_types_result]
            
            # Get node count
            node_count_result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = node_count_result.single()["count"]
            
            # Get relationship count
            rel_count_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = rel_count_result.single()["count"]
            
            return {
                "success": True,
                "database_info": dict(db_info) if db_info else {},
                "node_labels": labels,
                "relationship_types": rel_types,
                "node_count": node_count,
                "relationship_count": rel_count
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
def create_node(label: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new node in the Neo4j database.
    
    Args:
        label: The label for the node
        properties: Dictionary of properties for the node
    
    Returns:
        Dictionary containing the created node information
    """
    try:
        driver = get_neo4j_driver()
        
        # Build the CREATE query
        props_str = ", ".join([f"{key}: ${key}" for key in properties.keys()])
        query = f"CREATE (n:{label} {{{props_str}}}) RETURN n"
        
        with driver.session() as session:
            result = session.run(query, properties)
            created_node = result.single()["n"]
            
            return {
                "success": True,
                "node": dict(created_node),
                "labels": list(created_node.labels),
                "id": created_node.id
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "label": label,
            "properties": properties
        }

@mcp.tool()
def find_nodes(label: Optional[str] = None, properties: Optional[Dict[str, Any]] = None, limit: int = 10) -> Dict[str, Any]:
    """
    Find nodes in the Neo4j database.
    
    Args:
        label: Optional label to filter by
        properties: Optional properties to match
        limit: Maximum number of nodes to return (default: 10)
    
    Returns:
        Dictionary containing matching nodes
    """
    try:
        driver = get_neo4j_driver()
        
        # Build the MATCH query
        if label:
            match_clause = f"MATCH (n:{label})"
        else:
            match_clause = "MATCH (n)"
        
        where_clauses = []
        params = {"limit": limit}
        
        if properties:
            for key, value in properties.items():
                where_clauses.append(f"n.{key} = ${key}")
                params[key] = value
        
        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"{match_clause}{where_clause} RETURN n LIMIT $limit"
        
        with driver.session() as session:
            result = session.run(query, params)
            
            nodes = []
            for record in result:
                node = record["n"]
                nodes.append({
                    "properties": dict(node),
                    "labels": list(node.labels),
                    "id": node.id
                })
            
            return {
                "success": True,
                "nodes": nodes,
                "count": len(nodes),
                "query": query
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "label": label,
            "properties": properties
        }

# Cleanup function
def cleanup():
    """Clean up resources when server shuts down"""
    close_driver()

# Run the server
if __name__ == "__main__":
    mcp.run(transport="streamable-http")
