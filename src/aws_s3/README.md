# AWS S3 MCP Server

Seamlessly manage your AWS S3 buckets and objects directly through Claude using natural language. This Model Context Protocol (MCP) server enables your LLM to interact with S3 resources securely and efficiently.

## ✨ Features

- 📂 **List S3 Buckets**: View all accessible buckets in your AWS account
- 📋 **Browse Bucket Contents**: Explore objects within specific buckets
- ⬆️ **Upload Files**: Transfer local files to S3 with customizable access controls
- ⬇️ **Download Files**: Retrieve S3 objects to your local system
- 🗑️ **Delete Objects**: Remove unwanted files from your buckets
- 🔒 **Secure Access**: Restricted file operations within a designated local directory
- 🎯 **Natural Language Interface**: Use conversational commands instead of complex CLI syntax

## 📋 Prerequisites

Before getting started, ensure you have:

- **AWS Account** with S3 access
- **Docker** installed and running ([Download Docker](https://docs.docker.com/get-docker/))
- **Claude Desktop** application ([Download Claude](https://claude.ai/download))
- **Basic AWS IAM knowledge** for setting up permissions

## 🔧 AWS Setup

### Step 1: Create IAM Policy

Create a custom IAM policy with the following JSON configuration. This provides the minimum required permissions for S3 operations:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListAllBuckets",
      "Effect": "Allow",
      "Action": ["s3:ListAllMyBuckets"],
      "Resource": "*"
    },
    {
      "Sid": "ListObjectsInBucket",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::*"
    },
    {
      "Sid": "ObjectOperations",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObjectAcl",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::*/*"
    }
  ]
}
```

### Step 2: Create IAM User

1. **Create a new IAM user** in the AWS Console
2. **Attach the policy** created in Step 1 to this user
3. **Generate Access Keys** for programmatic access
4. **Save the credentials** securely (you'll need them for configuration)

> ⚠️ **Security Note**: Store your AWS credentials securely and never commit them to version control

## 🚀 Installation & Setup

### Step 1: Clone and Build

```bash
# Clone the repository
git clone https://github.com/thejasmeetsingh/mcp-servers.git

# Navigate to the AWS S3 MCP directory
cd mcp-servers/src/aws-s3/

# Build the Docker image
docker build -t mcp/aws-s3 .
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
    "aws-s3": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v",
        "<YOUR_LOCAL_PATH>:/data",
        "-e",
        "ACCESS_KEY_ID=<YOUR_AWS_ACCESS_KEY_ID>",
        "-e",
        "SECRET_ACCESS_KEY=<YOUR_AWS_SECRET_ACCESS_KEY>",
        "--name",
        "aws-s3-mcp",
        "mcp/aws-s3"
      ]
    }
  }
}
```

**Configuration Parameters:**

- `<YOUR_LOCAL_PATH>`: Local directory path where files will be stored/retrieved (e.g., `/Users/username/s3-files` or `C:\Users\username\s3-files`)
- `<YOUR_AWS_ACCESS_KEY_ID>`: Your AWS Access Key ID from Step 2
- `<YOUR_AWS_SECRET_ACCESS_KEY>`: Your AWS Secret Access Key from Step 2

### Step 4: Launch and Test

1. **Save** your configuration file
2. **Completely restart** Claude Desktop (quit and reopen the application)
3. **Test the connection** by asking Claude: _"Can you list my S3 buckets?"_

## 💡 Usage Examples

Once configured, you can interact with S3 using natural language:

### Basic Operations

```
📂 "Show me all my S3 buckets"
📋 "List the contents of my-project-bucket"
⬆️ "Upload report.pdf to my-documents-bucket"
⬇️ "Download the latest backup from my-backup-bucket"
🗑️ "Delete old-file.txt from my-temp-bucket"
```

### Advanced Operations

```
🔒 "Upload sensitive-data.json to private-bucket with private access"
📊 "Show me the contents of analytics-bucket and download the CSV files"
🔍 "Find all PDF files in my-documents-bucket"
```

## 🎥 Demo

[![](https://github.com/user-attachments/assets/5d2a15f9-cb45-42f8-9f59-a017127ddda0)](https://ja3-projects.s3.ap-south-1.amazonaws.com/aws-s3-mcp-1748640912.mp4)

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 🐳 Docker Issues

```bash
# Verify Docker installation
docker --version

# Check if Docker daemon is running
docker info

# View MCP server logs
docker logs aws-s3-mcp

# Remove and rebuild if needed
docker rmi mcp/aws-s3
docker build -t mcp/aws-s3 .
```

#### 🔐 Authentication Problems

- **Invalid Credentials**: Verify your AWS Access Key ID and Secret Access Key
- **Insufficient Permissions**: Ensure the IAM policy is correctly attached to your user
- **Region Issues**: The server uses default AWS region settings; configure AWS CLI if needed

#### 📁 File Path Issues

- **Windows Users**: Use forward slashes in paths (e.g., `C:/Users/username/s3-files`)
- **Permission Denied**: Ensure Docker has access to the specified directory
- **Path Not Found**: Verify the local directory exists before starting Claude

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

## ⚡ Performance Tips

- **Batch Operations**: Group multiple file operations when possible
- **Local Storage**: Ensure adequate disk space in your configured local directory
- **Network**: Stable internet connection required for reliable S3 operations

## 🔒 Security Best Practices

- **Principle of Least Privilege**: Only grant necessary S3 permissions
- **Credential Rotation**: Regularly rotate your AWS Access Keys
- **Local File Management**: Regularly clean up your local MCP directory
- **Audit Logs**: Monitor AWS CloudTrail for S3 API activity

---

_For more information about Model Context Protocol, visit the [official MCP documentation](https://modelcontextprotocol.io/introduction)_
