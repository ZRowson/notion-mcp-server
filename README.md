# Notion MCP Server

A Model Context Protocol (MCP) server that integrates with Notion, allowing AI assistants to interact with your Notion workspace through standardized tools and resources.

## Features

### Tools (Actions)
- **create_page**: Create a new page in your Notion workspace
- **update_page**: Update an existing page's content
- **search_pages**: Search for pages by title across your workspace
- **append_to_page**: Append content to an existing page
- **create_database_entry**: Add a new entry to a Notion database

### Resources (Data Access)
- **recent_pages**: Get a list of recently edited pages
- **page_content**: Read the content of a specific page

## Prerequisites

- Python 3.10 or higher
- A Notion account
- A Notion integration token

## Getting Your Notion API Key

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "+ New integration"
3. Give it a name (e.g., "MCP Server")
4. Select the workspace you want to integrate with
5. Click "Submit"
6. Copy the "Internal Integration Token" - this is your API key
7. **Important**: You must share pages/databases with your integration:
   - Open the page or database in Notion
   - Click the "..." menu in the top right
   - Scroll down to "Connections" or "Add connections"
   - Select your integration

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
# Using pip
pip install -e .

# Or using uv (recommended)
uv add "mcp[cli]"
```

3. Create a `.env` file in the project root:

```bash
NOTION_API_KEY=your_notion_integration_token_here
```

## Usage

### Running the Server Directly

```bash
python -m notion_mcp.server
```

### Using with Claude Desktop

Add this configuration to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "notion": {
      "command": "python",
      "args": ["-m", "notion_mcp.server"],
      "env": {
        "NOTION_API_KEY": "your_notion_integration_token_here"
      }
    }
  }
}
```

Or if you're using `uv`:

```json
{
  "mcpServers": {
    "notion": {
      "command": "uv",
      "args": ["run", "notion-mcp"],
      "env": {
        "NOTION_API_KEY": "your_notion_integration_token_here"
      }
    }
  }
}
```

### Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector python -m notion_mcp.server
```

## Example Usage

Once connected to Claude Desktop, you can ask things like:

- "Create a new page called 'Meeting Notes' in my Notion workspace"
- "Search for pages about 'project alpha'"
- "Show me my recently edited pages"
- "Append these action items to my meeting notes page"
- "Create a new entry in my tasks database"

## Architecture

The server implements the MCP specification and provides:

1. **Tools**: Functions that Claude can call to perform actions in Notion
2. **Resources**: Read-only access to Notion data
3. **Proper error handling**: Graceful handling of API errors and rate limits

## Security Notes

- Never commit your `.env` file or share your Notion API key
- The integration only has access to pages/databases you explicitly share with it
- All API calls are made over HTTPS
- Consider using environment variables for production deployments

## Troubleshooting

### "Could not find database" or "Could not find page"
- Make sure you've shared the page/database with your integration in Notion
- Check that the page/database ID is correct

### "Unauthorized" errors
- Verify your API key is correct in the `.env` file
- Ensure the integration has the necessary permissions

### Server not appearing in Claude Desktop
- Check that the config file path is correct
- Verify the Python path in the command
- Look at Claude Desktop logs for error messages

## Development

To extend this server:

1. Add new tools with the `@mcp.tool()` decorator
2. Add new resources with the `@mcp.resource()` decorator
3. Test with the MCP Inspector before deploying

## License

MIT License

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.
