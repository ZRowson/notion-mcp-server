# Notion MCP Server - Usage Examples

This document provides practical examples of how to use the Notion MCP Server with Claude Desktop.

## Prerequisites

Make sure you've:
1. Set up your Notion integration and gotten your API key
2. Shared relevant pages/databases with your integration
3. Configured Claude Desktop with the server
4. Restarted Claude Desktop

## Basic Examples

### 1. Creating a New Page

**User**: "Create a new page in Notion called 'Project Alpha' with some initial notes."

Claude will call the `create_page` tool with:
- title: "Project Alpha"
- content: Initial notes content
- parent_page_id: (optional, you may need to provide a parent page ID)

**Important**: For creating pages, you'll often need to provide a parent page ID. You can get these IDs by searching first.

### 2. Searching for Pages

**User**: "Find all my pages related to 'meeting notes'."

Claude will use the `search_pages` tool to find relevant pages.

**User**: "Show me pages that mention 'budget'."

### 3. Reading Page Content

**User**: "What's in my 'Weekly Goals' page?"

First, Claude will search for the page to get its ID, then use `get_page_content` to retrieve the full content.

### 4. Appending Content

**User**: "Add these action items to my Project Alpha page:
- Review design mockups
- Schedule team meeting
- Update timeline"

Claude will:
1. Search for "Project Alpha" to get the page ID
2. Use `append_to_page` to add the content

### 5. Working with Recent Pages

**User**: "What have I been working on recently in Notion?"

Claude will access the `recent_pages` resource to show you your recently edited pages.

## Advanced Examples

### Multi-Step Workflows

**User**: "Create a new page for my weekly planning, add today's date as the title, and populate it with sections for Goals, Tasks, and Notes."

Claude will:
1. Create the page with an appropriate title
2. Append multiple blocks for each section

### Database Operations

**User**: "Add a new task to my Tasks database with the name 'Review Q4 budget', status 'Todo', and due date next Friday."

For this to work, you need:
1. The database ID (you can find this in the database URL)
2. To know the exact property names in your database

Example command:
```
Create a database entry in database_id "xxx" with properties:
{
  "Name": {"title": [{"text": {"content": "Review Q4 budget"}}]},
  "Status": {"select": {"name": "Todo"}},
  "Due Date": {"date": {"start": "2024-12-27"}}
}
```

### Combining Search and Update

**User**: "Find my 'Daily Journal' page and add today's entry about the product launch."

Claude will:
1. Use `search_pages` to find the page
2. Use `append_to_page` to add the new entry

## Tips for Best Results

### 1. Be Specific with Page Names
- ✅ "Find my 'Weekly Planning - December 2024' page"
- ❌ "Find my planning page"

### 2. Provide Context
- ✅ "Create a meeting notes page for the Design Review meeting we're having tomorrow"
- ❌ "Create a page"

### 3. Use Page IDs When Available
If you have a page ID from a previous search, you can reference it:
- "Append content to page ID abc123xyz"

### 4. Understand Database Schema
For database operations, you need to know:
- Property names (case-sensitive)
- Property types (title, select, date, etc.)
- Valid values (for select/multi-select fields)

## Common Issues and Solutions

### Issue: "Could not find page"
**Solution**: Make sure you've shared the page with your integration in Notion:
1. Open the page in Notion
2. Click "..." menu → "Connections"
3. Add your integration

### Issue: "Invalid parent"
**Solution**: Either:
- Provide a valid parent_page_id when creating pages
- Or let the server find a recent page to use as parent

### Issue: Database entry creation fails
**Solution**: Check that:
- The database is shared with your integration
- Property names match exactly (case-sensitive)
- Property types are correct
- You're using the correct format for each property type

## Property Format Reference

### Common Property Types

**Title**:
```json
{"title": [{"text": {"content": "Your text"}}]}
```

**Rich Text**:
```json
{"rich_text": [{"text": {"content": "Your text"}}]}
```

**Select** (single choice):
```json
{"select": {"name": "Option Name"}}
```

**Multi-select** (multiple choices):
```json
{"multi_select": [{"name": "Option 1"}, {"name": "Option 2"}]}
```

**Date**:
```json
{"date": {"start": "2024-12-31"}}
```

**Date Range**:
```json
{"date": {"start": "2024-12-01", "end": "2024-12-31"}}
```

**Checkbox**:
```json
{"checkbox": true}
```

**Number**:
```json
{"number": 42}
```

**URL**:
```json
{"url": "https://example.com"}
```

**Email**:
```json
{"email": "user@example.com"}
```

**Phone**:
```json
{"phone_number": "+1234567890"}
```

## Next Steps

- Explore the [Notion API documentation](https://developers.notion.com/) for more details
- Create custom workflows by combining multiple tools
- Share feedback on what features you'd like to see added
