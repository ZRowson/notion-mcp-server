# Remote MCP Server Deployment Guide

This guide explains how to run the Notion MCP server on a remote RHEL 10 machine and connect to it from your local Claude Desktop application.

## Architecture Overview

```
┌─────────────────┐         HTTPS          ┌──────────────────┐
│                 │  ───────────────────>   │                  │
│ Claude Desktop  │                         │  Remote Server   │
│   (Your Mac/PC) │  <───────────────────   │   (RHEL 10)      │
│                 │         SSE             │                  │
└─────────────────┘                         └──────────────────┘
```

## Step 1: Setup on Remote Server

### 1.1 Install Dependencies

```bash
# SSH into your RHEL server
ssh username@your-server-ip

# Navigate to where you want to install
cd ~

# Extract the project (if you used SCP)
tar -xzf notion-mcp-server.tar.gz
cd notion-mcp-server

# Install Python 3.10+ if needed
sudo dnf install python3.11 python3-pip

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 1.2 Configure Environment

```bash
# Create .env file
cat > .env << 'EOF'
NOTION_API_KEY=your_notion_integration_token_here
MCP_HOST=0.0.0.0
MCP_PORT=8000
EOF

# Edit with your actual Notion API key
nano .env
```

### 1.3 Test the Server Locally

```bash
# Run the HTTP server
python -m notion_mcp.server_http

# You should see:
# INFO:     Started server process
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 2: Configure Firewall

```bash
# Allow port 8000 through firewall
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-ports
```

## Step 3: Run as a Service (Recommended)

### 3.1 Create systemd Service

```bash
sudo nano /etc/systemd/system/notion-mcp.service
```

Add this content:

```ini
[Unit]
Description=Notion MCP Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/notion-mcp-server
Environment="PATH=/home/your-username/notion-mcp-server/venv/bin"
ExecStart=/home/your-username/notion-mcp-server/venv/bin/python -m notion_mcp.server_http
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3.2 Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable notion-mcp

# Start the service
sudo systemctl start notion-mcp

# Check status
sudo systemctl status notion-mcp

# View logs
sudo journalctl -u notion-mcp -f
```

## Step 4: Configure Claude Desktop

### 4.1 Find Your Config File

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### 4.2 Add Server Configuration

Edit the config file and add:

```json
{
  "mcpServers": {
    "notion-remote": {
      "url": "http://your-server-ip:8000/sse",
      "transport": {
        "type": "sse"
      }
    }
  }
}
```

Replace `your-server-ip` with your actual server's IP address.

### 4.3 Restart Claude Desktop

Completely quit and restart Claude Desktop to pick up the new configuration.

## Step 5: Test the Connection

In Claude Desktop, try asking:

```
"Can you search my Notion pages for 'meeting notes'?"
```

If configured correctly, Claude will use the remote MCP server to search your Notion workspace.

## Security Considerations

### Option A: Use SSH Tunnel (Most Secure)

Instead of exposing the server directly, create an SSH tunnel:

```bash
# On your local machine
ssh -L 8000:localhost:8000 username@your-server-ip
```

Then configure Claude Desktop to use:
```json
{
  "mcpServers": {
    "notion-remote": {
      "url": "http://localhost:8000/sse",
      "transport": {
        "type": "sse"
      }
    }
  }
}
```

### Option B: Use Nginx with HTTPS (Production)

1. **Install Nginx and Certbot:**
```bash
sudo dnf install nginx certbot python3-certbot-nginx
```

2. **Configure Nginx:**
```bash
sudo nano /etc/nginx/conf.d/notion-mcp.conf
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;
    }
}
```

3. **Get SSL Certificate:**
```bash
sudo certbot --nginx -d your-domain.com
```

4. **Update Claude Desktop config:**
```json
{
  "mcpServers": {
    "notion-remote": {
      "url": "https://your-domain.com/sse",
      "transport": {
        "type": "sse"
      }
    }
  }
}
```

### Option C: Add Authentication (Advanced)

Modify the server to require an API key:

```python
# In server_http.py, add this before the main() function:

from fastapi import Header, HTTPException

@mcp.middleware("http")
async def verify_api_key(request, call_next):
    api_key = request.headers.get("X-API-Key")
    if api_key != os.getenv("MCP_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return await call_next(request)
```

Add to `.env`:
```
MCP_API_KEY=your-secret-key-here
```

Update Claude Desktop config:
```json
{
  "mcpServers": {
    "notion-remote": {
      "url": "https://your-domain.com/sse",
      "transport": {
        "type": "sse"
      },
      "headers": {
        "X-API-Key": "your-secret-key-here"
      }
    }
  }
}
```

## Troubleshooting

### Server Not Accessible

```bash
# Check if server is running
sudo systemctl status notion-mcp

# Check if port is listening
sudo netstat -tlnp | grep 8000

# Check firewall
sudo firewall-cmd --list-all

# Test from server itself
curl http://localhost:8000/sse
```

### Claude Desktop Can't Connect

1. Verify the URL is correct
2. Check server logs: `sudo journalctl -u notion-mcp -f`
3. Try accessing the URL in a web browser
4. Verify firewall allows incoming connections
5. Check Claude Desktop logs (Help → View Logs)

### Permission Denied

```bash
# Ensure .env file is readable
chmod 600 .env

# Ensure service has correct user
sudo systemctl edit notion-mcp
```

## Monitoring

### View Real-time Logs

```bash
sudo journalctl -u notion-mcp -f
```

### Check Resource Usage

```bash
# CPU and memory
top -p $(pgrep -f notion_mcp)

# Detailed stats
htop
```

## Updating the Server

```bash
# Stop the service
sudo systemctl stop notion-mcp

# Update code
cd ~/notion-mcp-server
git pull  # if using git
# or re-upload files

# Restart
sudo systemctl start notion-mcp
```

## Alternative: Quick Test with ngrok

For quick testing without configuring firewall/DNS:

```bash
# On the server
./ngrok http 8000

# Use the ngrok URL in Claude Desktop:
# https://xxxx-xx-xx-xxx-xx.ngrok-free.app/sse
```

Note: ngrok free tier has limitations and URLs change on restart.

## Summary

**Simplest**: SSH tunnel (Option A in Security)
**Production**: Nginx with HTTPS (Option B)
**Quick Test**: ngrok

The SSH tunnel approach is recommended for personal use as it's secure and doesn't require exposing ports or configuring certificates.
