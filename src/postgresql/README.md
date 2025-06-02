# PostgreSQL MCP Server

A Model Context Protocol (MCP) server that enables your favorite LLM to seamlessly interact with PostgreSQL databases. Execute DDL and DML operations through natural language queries with built-in validation and error handling.

## ✨ Features

**Database Operations**

- Execute DDL operations (CREATE, ALTER, DROP tables/schemas)
- Perform DML operations (SELECT, INSERT, UPDATE, DELETE)
- Transaction support for complex operations

**Query Intelligence**

- Syntax validation before execution
- Natural language to SQL translation
- Detailed error reporting and debugging assistance
- Query optimization suggestions

**Safety & Security**

- Query validation prevents malformed SQL execution
- Containerized environment for secure database interactions
- Configurable connection parameters

## 🛠️ Prerequisites

Before getting started, ensure you have:

- Docker and Docker Compose installed
- Claude Desktop application
- Basic familiarity with PostgreSQL (helpful but not required)

## 🚀 Quick Start Guide

### Step 1: Clone and Setup the Environment

```bash
# Clone the repository
git clone https://github.com/thejasmeetsingh/mcp-servers.git

# Navigate to the PostgreSQL MCP directory
cd mcp-servers/src/postgresql/

# Create a shared Docker network for container communication
docker network create shared-network

# Launch PostgreSQL server with Docker Compose
docker-compose up -d

# Build the MCP server Docker image
docker build -t mcp/postgresql .
```

**What's happening here?** We're setting up a containerized PostgreSQL environment that the MCP server will connect to. The shared network allows secure communication between containers.

### Step 2: Locate Your Claude Desktop Configuration

Find your configuration file based on your operating system:

- 🪟 **Windows**: `%APPDATA%\Claude Desktop\claude_desktop_config.json`
- 🍎 **macOS**: `~/Library/Application Support/Claude Desktop/claude_desktop_config.json`
- 🐧 **Linux**: `~/.config/Claude Desktop/claude_desktop_config.json`

**Pro tip:** If the file doesn't exist, create it as an empty JSON object: `{}`

### Step 3: Configure the MCP Server

Add this configuration to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "postgresql": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "--network=shared-network",
        "-e",
        "DB_NAME=your_database_name",
        "-e",
        "DB_USER=your_username",
        "-e",
        "DB_PASSWORD=your_password",
        "-e",
        "DB_HOST=db",
        "-e",
        "DB_PORT=5432",
        "--name",
        "postgresql-mcp",
        "mcp/postgresql"
      ]
    }
  }
}
```

**Configuration Parameters:**

- `DB_NAME`: Your PostgreSQL database name
- `DB_USER`: Database username (check your .env file)
- `DB_PASSWORD`: Database password (check your .env file)
- `DB_HOST`: Container hostname (use `db` for the docker-compose setup)
- `DB_PORT`: PostgreSQL port (default: `5432`)

### Step 4: Launch and Verify

1. **Save** your configuration file
2. **Completely restart** Claude Desktop (quit and reopen the application)
3. **Verify the connection** by asking Claude:
   - _"Can you show me all tables in my database?"_
   - _"What's the current database schema?"_
   - _"Create a simple test table for me"_

## 💡 Usage Examples

Once configured, you can interact with your PostgreSQL database through natural language:

**Schema Exploration:**

- "What tables exist in my database?"
- "Describe the structure of the users table"
- "Show me all foreign key relationships"

**Data Operations:**

- "Insert a new user with name 'John' and email 'john@example.com'"
- "Find all orders from the last 30 days"
- "Update the status of order #12345 to 'shipped'"

**Database Management:**

- "Create a backup table of my current users"
- "Add an index on the email column for better performance"
- "Show me the execution plan for this complex query"

## 🔧 Troubleshooting

**Connection Issues:**

- Ensure Docker containers are running: `docker ps`
- Check network connectivity: `docker network ls`
- Verify database credentials in your configuration

**Claude Desktop Not Recognizing MCP Server:**

- Confirm JSON syntax in configuration file
- Restart Claude Desktop completely
- Check that the Docker image was built successfully

**Query Execution Problems:**

- Review error messages - the server provides detailed feedback
- Verify your SQL syntax if writing raw queries
- Check database permissions for your user account

---

_For more information about Model Context Protocol, visit the [official MCP documentation](https://modelcontextprotocol.io/introduction)_
