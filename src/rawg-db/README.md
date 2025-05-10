# RAWG Database MCP

Access and explore the RAWG Video Game Database through Claude's Model-Consumer-Producer (MCP) interface.

## Overview

This tool allows you to query comprehensive video game information directly through Claude. It uses Redis caching to minimize API calls and prevent throttling errors from the RAWG service.

## Prerequisites

- Docker installed on your system
- Claude Desktop application
- RAWG API key (obtainable from [rawg.io/apidocs](https://rawg.io/apidocs))

## Setup Instructions

1.  Create Docker Network and Redis Container

    First, establish a shared Docker network and deploy a Redis container for caching:

    **Note:** Redis is being as cache to store redundant API responses which do not change often and it significantly reduce our API calls to the rawg service. Thus the changes of getting throttling errors from the service are very less.

    ```bash
     # Create a shared Docker network
     docker network create shared-network

     # Launch Redis container on the network
     docker run -d --name redis --network shared-network redis:alpine
    ```

2.  Configure Claude Desktop
    Locate and modify your `claude_desktop_config.json` file:

    **File Location:**

    - **Windows:** `%APPDATA%\Claude Desktop\claude_desktop_config.json`
    - **macOS:** `~/Library/Application Support/Claude Desktop/-claude_desktop_config.json`
    - **Linux:** `~/.config/Claude Desktop/claude_desktop_config.json`

    **Configuration:**

    ```json
    {
      "mcpServers": {
        "rawg-db": {
          "command": "docker",
          "args": [
            "run",
            "-i",
            "--rm",
            "-e",
            "RAWG_API_BASE_URL=https://api.rawg.io/api",
            "-e",
            "RAWG_API_KEY=<API KEY>",
            "--network",
            "shared-network",
            "--name",
            "rawg-db",
            "mcp/rawg-db"
          ]
        }
      }
    }
    ```

    > **Important:** Replace <YOUR_API_KEY> with your actual RAWG API key.

3.  Restart Claude
    After saving your configuration, restart the Claude Desktop application to apply the changes.

    **Usage**

    Once configured, you can ask Claude questions about video games, such as:

    - "What are the top-rated games of 2023?"
    - "Tell me about the developer of Elden Ring"
    - "What platforms is Cyberpunk 2077 available on?"

[![](https://github.com/user-attachments/assets/5d2a15f9-cb45-42f8-9f59-a017127ddda0)](https://ja3-projects.s3.ap-south-1.amazonaws.com/rawg-db-mcp.mp4)

## Troubleshooting

If you encounter issues:

- Verify Docker is running
- Confirm Redis container is active with `docker container ls`
- Check API key validity
- Inspect Docker logs with docker logs `rawg-db`

---

_For more information about Claude's MCP capabilities, please refer to the [official documentation](https://modelcontextprotocol.io/introduction)_
