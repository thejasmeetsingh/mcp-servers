# AWS CloudWatch Logs MCP Server

**Seamlessly manage your AWS CloudWatch Logs through Claude using natural language**
_Transform complex CLI commands into simple conversations_

## 🌟 Overview

This Model Context Protocol (MCP) server bridges the gap between Claude and your AWS CloudWatch Logs, enabling you to query, analyze, and manage your log data using natural language. No more wrestling with complex AWS CLI syntax or remembering obscure command parameters.

### What You Can Do

- 📋 **Browse Log Groups**: "Show me all my application log groups"
- 🔍 **Explore Log Streams**: "What log streams exist for my web-app?"
- 📊 **Analyze Log Events**: "Get the last 100 error logs from my API service"
- 🕒 **Time-based Queries**: "Show me logs from the last 24 hours"
- 💬 **Natural Language**: Use conversational commands instead of memorizing CLI syntax

## 🚀 Quick Start

### Prerequisites Checklist

Before diving in, make sure you have:

- [ ] **AWS Account** with CloudWatch Logs access
- [ ] **Docker** installed and running ([Get Docker](https://docs.docker.com/get-docker/))
- [ ] **Claude Desktop** application ([Download here](https://claude.ai/download))
- [ ] **10 minutes** for setup

### 1. AWS Configuration

#### Create IAM Policy

Navigate to AWS Console → IAM → Policies → Create Policy, then use this JSON:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudWatchLogsReadAccess",
      "Effect": "Allow",
      "Action": [
        "logs:ListLogGroups",
        "logs:DescribeLogStreams",
        "logs:DescribeLogGroups",
        "logs:GetLogEvents",
        "logs:FilterLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

#### Create IAM User

1. **Create User**: AWS Console → IAM → Users → Create User
2. **Attach Policy**: Select the policy you just created
3. **Generate Keys**: Create Access Key → Command Line Interface (CLI)
4. **Save Credentials**: You'll need these in the next step

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/thejasmeetsingh/mcp-servers.git

# Navigate to the CloudWatch MCP directory
cd mcp-servers/src/aws-cloudwatch/

# Build the Docker image
docker build -t mcp/aws-cw-logs .
```

### Step 2: Configure Claude Desktop

Locate your Claude Desktop configuration file based on your operating system:

- 🪟 **Windows**: `%APPDATA%\Claude Desktop\claude_desktop_config.json`
- 🍎 **macOS**: `~/Library/Application Support/Claude Desktop/claude_desktop_config.json`
- 🐧 **Linux**: `~/.config/Claude Desktop/claude_desktop_config.json`

### Step 3: Add MCP Server Configuration

Add the following configuration to your `claude_desktop_config.json` file:

```json
{
  "mcpServers": {
    "aws-cw-logs": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "AWS_ACCESS_KEY_ID=<YOUR_AWS_ACCESS_KEY_ID>",
        "-e",
        "AWS_SECRET_ACCESS_KEY=<YOUR_AWS_SECRET_ACCESS_KEY>",
        "-e",
        "AWS_DEFAULT_REGION=<YOUR_AWS_PREFERRED_REGION>",
        "--name",
        "aws-cw-logs-mcp",
        "mcp/aws-cw-logs"
      ]
    }
  }
}
```

**Configuration Parameters:**

- `<YOUR_AWS_ACCESS_KEY_ID>`: Your AWS Access Key ID from Step 2
- `<YOUR_AWS_SECRET_ACCESS_KEY>`: Your AWS Secret Access Key from Step 2
- `<YOUR_AWS_DEFAULT_REGION>`: Your preferred AWS region

### 4. Test Your Setup

1. **Save** your configuration file
2. **Restart** Claude Desktop completely (quit and reopen)
3. **Test** by asking Claude: _"Can you list all my CloudWatch log groups?"_

If you see your log groups, you're all set! 🎉

## 💡 Usage Examples

Once configured, interact with your logs naturally:

### Exploring Your Logs

```
"What log groups do I have?"
"Show me the log streams for my web-application group"
"How many log groups contain the word 'production'?"
```

### Analyzing Log Data

```
"Get the latest 50 log entries from my API service"
"Show me error logs from the last 2 hours"
"Find all logs containing 'database connection' from today"
```

### Troubleshooting Scenarios

```
"Help me find recent errors in my payment service logs"
"What happened in my application logs around 2 PM yesterday?"
"Show me all WARNING and ERROR level logs from the last hour"
```

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 🐳 Docker Issues

```bash
# Verify Docker installation
docker --version

# Check if Docker daemon is running
docker info

# View MCP server logs
docker logs aws-cw-logs-mcp

# Remove and rebuild if needed
docker rmi mcp/aws-cw-logs
docker build -t mcp/aws-cw-logs .
```

#### 🔐 Authentication Problems

- **Invalid Credentials**: Verify your AWS Access Key ID and Secret Access Key
- **Insufficient Permissions**: Ensure the IAM policy is correctly attached to your user
- **Region Issues**: The server uses default AWS region settings; configure AWS CLI if needed

#### 🔌 Connection Issues

- **MCP Server Not Found**: Restart Claude Desktop completely after configuration changes
- **Docker Container Not Starting**: Check system resources and Docker daemon status
- **Configuration Syntax**: Validate JSON syntax in `claude_desktop_config.json`

### Getting Help

If you encounter issues not covered here:

1. **Check the logs**: Review Docker container logs for error details
2. **Verify configuration**: Double-check your `claude_desktop_config.json` syntax
3. **Test AWS access**: Use AWS CLI to verify your credentials work independently
4. **GitHub Issues**: Report bugs or request features on the [project repository](https://github.com/thejasmeetsingh/mcp-servers)

## 🔒 Security Best Practices

- **Principle of Least Privilege**: Only grant necessary CloudWatch Logs permissions
- **Credential Rotation**: Regularly rotate your AWS Access Keys
- **Audit Logs**: Monitor AWS CloudTrail for CloudWatch API activity

---

_For more information about Model Context Protocol, visit the [official MCP documentation](https://modelcontextprotocol.io/introduction)_
