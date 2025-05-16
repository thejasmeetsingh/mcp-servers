# MCP For Web Search

A Model Context Protocol (MCP) server implementation that empowers Large Language Models (LLMs) with web search capabilities through the Brave Search API. Additionally, it enables your LLM to extract and process full content from web pages using the Tavily API, delivering more comprehensive results compared to standard web search snippets.

## Features

- **Web Search Integration**: Query the internet in real-time using Brave Search API
- **Content Extraction**: Retrieve and analyze full webpage contents via Tavily API
- **Seamless Claude Integration**: Works directly with Claude Desktop application or any other MCP client.
- **Docker-based Deployment**: Simple containerized setup for cross-platform compatibility

## Prerequisites

- Docker installed on your system
- Claude Desktop application
- Brave API key (obtainable from [Brave Web Search Dashboard](https://api-dashboard.search.brave.com/app/documentation/web-search/get-started))
- Tavily API key (obtainable from [Tavily](https://docs.tavily.com/documentation/quickstart))

## Setup Instructions

1. Build from source:

   ```bash
   git clone https://github.com/thejasmeetsingh/mcp-servers.git
   cd src/web-search/
   docker build -t mcp/web-search .
   ```

2. Configure Claude Desktop
   Locate and modify your `claude_desktop_config.json` file:

   **File Location:**

   - **Windows:** `%APPDATA%\Claude Desktop\claude_desktop_config.json`
   - **macOS:** `~/Library/Application Support/Claude Desktop/-claude_desktop_config.json`
   - **Linux:** `~/.config/Claude Desktop/claude_desktop_config.json`

   **Configuration:**

   ```json
   {
     "mcpServers": {
       "web-search": {
         "command": "docker",
         "args": [
           "run",
           "-i",
           "--rm",
           "-e",
           "BRAVE_API_KEY=<Brave API KEY>",
           "-e",
           "TAVILY_API_KEY=<TAVILY API KEY>",
           "--name",
           "web-search",
           "mcp/web-search"
         ]
       }
     }
   }
   ```

   > **Important**: Replace `<Brave API KEY>` and `<TAVILY API KEY>` with your actual API keys.

3. Restart Claude
   After saving your configuration, restart the Claude Desktop application to apply the changes.

   **Usage**

   Once configured, you can ask Claude to perform web searches with natural language queries like:

   - "Search for the latest developments in AI"
   - "Find information about upcoming Marvel movies"
   - "Look up recent global news"
   - "Research quantum computing advancements"
   - "Search for healthy dinner recipes"

[![](https://github.com/user-attachments/assets/5d2a15f9-cb45-42f8-9f59-a017127ddda0)](https://ja3-projects.s3.ap-south-1.amazonaws.com/web-search-mcp.mp4)

## Troubleshooting

If you encounter issues:

- Verify Docker is running
- Check API key validity
- Inspect Docker logs with docker logs `web-search`
- Confirm the JSON syntax in your config file is correct

---

_For more information about Claude's MCP capabilities, please refer to the [official documentation](https://modelcontextprotocol.io/introduction)_
