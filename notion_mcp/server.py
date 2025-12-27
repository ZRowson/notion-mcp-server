"""
Notion MCP Server

This module implements a Model Context Protocol server that provides
integration with Notion, allowing AI assistants to create, read, update,
and search Notion pages and databases.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

# Configure logging to stderr (important for MCP stdio transport)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("notion-mcp-server")

# Initialize Notion client
notion_api_key = os.getenv("NOTION_API_KEY")
if not notion_api_key:
    logger.error("NOTION_API_KEY environment variable not set")
    raise ValueError("NOTION_API_KEY must be set in environment variables")

notion = Client(auth=notion_api_key)


# ============================================================================
# TOOLS (Actions that Claude can perform)
# ============================================================================

@mcp.tool()
def create_page(title: str, content: str, parent_page_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new page in Notion.
    
    Args:
        title: The title of the new page
        content: The text content to add to the page
        parent_page_id: Optional ID of the parent page. If not provided, creates a top-level page
    
    Returns:
        Dictionary with the created page's ID and URL
    """
    try:
        # Build the parent structure
        if parent_page_id:
            parent = {"page_id": parent_page_id}
        else:
            # Search for a page to use as parent, or you can configure a default page ID
            parent = {"page_id": parent_page_id} if parent_page_id else {"type": "page_id", "page_id": ""}
        
        # Create page properties
        properties = {
            "title": {
                "title": [
                    {
                        "text": {
                            "content": title
                        }
                    }
                ]
            }
        }
        
        # Create page content (children blocks)
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": content
                            }
                        }
                    ]
                }
            }
        ]
        
        # Make API call - if no parent_page_id, we need to handle differently
        if parent_page_id:
            response = notion.pages.create(
                parent=parent,
                properties=properties,
                children=children
            )
        else:
            # For top-level pages, we need a workspace parent or database parent
            # This will require user to specify or configure a default database/page
            logger.warning("No parent_page_id provided. Page creation may fail without a parent.")
            # Try to search for recent pages and use the first one as parent
            search_results = notion.search(filter={"property": "object", "value": "page"}, page_size=1)
            if search_results.get("results"):
                parent = {"page_id": search_results["results"][0]["id"]}
                response = notion.pages.create(
                    parent=parent,
                    properties=properties,
                    children=children
                )
            else:
                return {
                    "error": "No parent page specified and no existing pages found. Please provide a parent_page_id."
                }
        
        return {
            "success": True,
            "page_id": response["id"],
            "url": response["url"],
            "message": f"Page '{title}' created successfully"
        }
    
    except APIResponseError as e:
        logger.error(f"Notion API error: {e}")
        return {
            "success": False,
            "error": f"Notion API error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error creating page: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def search_pages(query: str, page_size: int = 10) -> Dict[str, Any]:
    """
    Search for pages in Notion by title or content.
    
    Args:
        query: The search query string
        page_size: Maximum number of results to return (default: 10)
    
    Returns:
        Dictionary containing search results with page titles, IDs, and URLs
    """
    try:
        # Search for pages
        response = notion.search(
            query=query,
            filter={"property": "object", "value": "page"},
            page_size=page_size
        )
        
        # Format results
        results = []
        for page in response.get("results", []):
            title = "Untitled"
            if "properties" in page and "title" in page["properties"]:
                title_property = page["properties"]["title"]
                if title_property.get("title"):
                    title = title_property["title"][0]["plain_text"]
            elif "properties" in page:
                # Try to find any title field
                for prop_name, prop_value in page["properties"].items():
                    if prop_value.get("type") == "title" and prop_value.get("title"):
                        title = prop_value["title"][0]["plain_text"]
                        break
            
            results.append({
                "id": page["id"],
                "title": title,
                "url": page["url"],
                "last_edited": page.get("last_edited_time", "Unknown")
            })
        
        return {
            "success": True,
            "count": len(results),
            "results": results
        }
    
    except APIResponseError as e:
        logger.error(f"Notion API error: {e}")
        return {
            "success": False,
            "error": f"Notion API error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error searching pages: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def get_page_content(page_id: str) -> Dict[str, Any]:
    """
    Retrieve the content of a specific Notion page.
    
    Args:
        page_id: The ID of the page to retrieve
    
    Returns:
        Dictionary containing the page title and content blocks
    """
    try:
        # Get page properties
        page = notion.pages.retrieve(page_id=page_id)
        
        # Extract title
        title = "Untitled"
        if "properties" in page:
            for prop_name, prop_value in page["properties"].items():
                if prop_value.get("type") == "title" and prop_value.get("title"):
                    title = prop_value["title"][0]["plain_text"]
                    break
        
        # Get page blocks (content)
        blocks_response = notion.blocks.children.list(block_id=page_id)
        
        # Extract text content from blocks
        content_blocks = []
        for block in blocks_response.get("results", []):
            block_type = block.get("type")
            block_content = block.get(block_type, {})
            
            # Extract text from rich_text fields
            if "rich_text" in block_content:
                text = "".join([
                    rt.get("plain_text", "") 
                    for rt in block_content["rich_text"]
                ])
                if text:
                    content_blocks.append({
                        "type": block_type,
                        "text": text
                    })
        
        return {
            "success": True,
            "page_id": page_id,
            "title": title,
            "url": page["url"],
            "content": content_blocks,
            "last_edited": page.get("last_edited_time")
        }
    
    except APIResponseError as e:
        logger.error(f"Notion API error: {e}")
        return {
            "success": False,
            "error": f"Notion API error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error retrieving page content: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def append_to_page(page_id: str, content: str) -> Dict[str, Any]:
    """
    Append new content to an existing Notion page.
    
    Args:
        page_id: The ID of the page to append to
        content: The text content to append
    
    Returns:
        Dictionary indicating success or failure
    """
    try:
        # Create a new paragraph block
        new_block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": content
                        }
                    }
                ]
            }
        }
        
        # Append the block to the page
        notion.blocks.children.append(
            block_id=page_id,
            children=[new_block]
        )
        
        return {
            "success": True,
            "message": f"Content appended to page {page_id}"
        }
    
    except APIResponseError as e:
        logger.error(f"Notion API error: {e}")
        return {
            "success": False,
            "error": f"Notion API error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error appending to page: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def update_page(page_id: str, title: Optional[str] = None, archived: Optional[bool] = None) -> Dict[str, Any]:
    """
    Update a Notion page's properties.
    
    Args:
        page_id: The ID of the page to update
        title: Optional new title for the page
        archived: Optional boolean to archive/unarchive the page
    
    Returns:
        Dictionary indicating success or failure
    """
    try:
        update_data = {}
        
        if title is not None:
            update_data["properties"] = {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }
        
        if archived is not None:
            update_data["archived"] = archived
        
        if not update_data:
            return {
                "success": False,
                "error": "No update parameters provided"
            }
        
        response = notion.pages.update(page_id=page_id, **update_data)
        
        return {
            "success": True,
            "page_id": response["id"],
            "url": response["url"],
            "message": "Page updated successfully"
        }
    
    except APIResponseError as e:
        logger.error(f"Notion API error: {e}")
        return {
            "success": False,
            "error": f"Notion API error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error updating page: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
def create_database_entry(database_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new entry in a Notion database.
    
    Args:
        database_id: The ID of the database to add an entry to
        properties: Dictionary of properties for the new entry (structure depends on database schema)
    
    Returns:
        Dictionary with the created entry's ID and URL
    
    Example properties format:
        {
            "Name": {"title": [{"text": {"content": "Task name"}}]},
            "Status": {"select": {"name": "In Progress"}},
            "Due Date": {"date": {"start": "2024-12-31"}}
        }
    """
    try:
        response = notion.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )
        
        return {
            "success": True,
            "page_id": response["id"],
            "url": response["url"],
            "message": "Database entry created successfully"
        }
    
    except APIResponseError as e:
        logger.error(f"Notion API error: {e}")
        return {
            "success": False,
            "error": f"Notion API error: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error creating database entry: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# RESOURCES (Read-only data access)
# ============================================================================

@mcp.resource("notion://recent-pages")
def get_recent_pages() -> str:
    """
    Get a list of recently edited pages in the Notion workspace.
    
    Returns:
        Formatted string with recent pages information
    """
    try:
        response = notion.search(
            filter={"property": "object", "value": "page"},
            sort={"direction": "descending", "timestamp": "last_edited_time"},
            page_size=20
        )
        
        output = ["# Recently Edited Pages\n"]
        
        for page in response.get("results", []):
            title = "Untitled"
            if "properties" in page:
                for prop_name, prop_value in page["properties"].items():
                    if prop_value.get("type") == "title" and prop_value.get("title"):
                        title = prop_value["title"][0]["plain_text"]
                        break
            
            output.append(f"- **{title}**")
            output.append(f"  - ID: `{page['id']}`")
            output.append(f"  - URL: {page['url']}")
            output.append(f"  - Last edited: {page.get('last_edited_time', 'Unknown')}\n")
        
        return "\n".join(output)
    
    except Exception as e:
        logger.error(f"Error getting recent pages: {e}")
        return f"Error retrieving recent pages: {str(e)}"


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the MCP server."""
    logger.info("Starting Notion MCP Server")
    mcp.run()


if __name__ == "__main__":
    main()
