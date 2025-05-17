# Google Calendar MCP

A Model Context Protocol (MCP) server implementation that empowers Large Language Models (LLMs) with Google Calendar management capabilities. Seamlessly integrate Claude with your personal or work calendar to enhance productivity.

## Features

- **View Schedule:** Get a comprehensive list of upcoming events
- **Search Events:** Find specific events using keywords
- **Event Management:** Add, retrieve, update, and delete calendar events
- **Seamless Authentication:** Simplified Google account authorization process
- **Automatic Token Refresh:** Google authentication tokens are automatically refreshed
- **Docker-based:** Easy deployment with containerization
- **Claude Integration:** Natural language interface to your calendar

## Prerequisites

- Docker installed on your system
- Claude Desktop application
- Google Cloud Console project with OAuth credentials ([Setup Guide](https://developers.google.com/identity/protocols/oauth2/web-server#python_6))

## Setup Instructions

### 1. Build from source:

```bash
git clone https://github.com/thejasmeetsingh/mcp-servers.git
cd src/calendar/
docker build -t mcp/calendar .
```

### 2. Configure Claude Desktop

Locate and modify your `claude_desktop_config.json` file:

**File Location:**

- **Windows:** `%APPDATA%\Claude Desktop\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude Desktop/-claude_desktop_config.json`
- **Linux:** `~/.config/Claude Desktop/claude_desktop_config.json`

**Configuration:**

```json
{
  "mcpServers": {
    "calendar": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--name", "calendar", "mcp/calendar"]
    }
  }
}
```

### 3. Google OAuth Setup

1. Create a project in Google Cloud Console
2. Enable the Google Calendar API
3. Create OAuth credentials (Web application type)
4. Add authorized redirect URIs (typically http://localhost:8080)
5. Download the credentials JSON file 9. Run the auth.py script for easily retrieving your google credentials.

### 4. Restart Claude

After saving your configuration, restart the Claude Desktop application to apply the changes.

**Example Usage**

Once configured, interact with your Google Calendar using natural language:

- **View Schedule**: "Can you check my schedule and tell me what I have lined up for this week?"
- **Create Event**: "I have a dentist appointment from 2 PM to 3 PM next Tuesday. Please add it to my calendar."
- **Find Event**: "Do I have any meetings scheduled with Alex this month?"
- **Update Event**: "Please reschedule my dentist appointment to start at 2:30 PM instead."
- **Delete Event**: "Please cancel my meeting with the marketing team tomorrow."
- **Get Details**: "What's on my calendar for May 20th?"

[![](https://github.com/user-attachments/assets/5d2a15f9-cb45-42f8-9f59-a017127ddda0)](https://ja3-projects.s3.ap-south-1.amazonaws.com/calendar-mcp.mp4)

## Troubleshooting

If you encounter issues:

- **Connection Problems**: Verify Docker is running and the container starts successfully
- **Authentication Errors**: Check your Google OAuth credentials and ensure proper scopes
- **Calendar Access Issues**: Verify your Google account has appropriate Calendar permissions
- **Container Issues**: Inspect Docker logs with `docker logs calendar`
- **Configuration Problems**: Confirm the JSON syntax in your config file is correct
- **Permission Denied**: Ensure proper file permissions for credential storage

## Security Considerations

- Your Google credentials are stored locally
- The MCP server runs in a sandboxed Docker container
- No data is sent to third-party services beyond Google's APIs
- Consider using a dedicated Google account for sensitive calendar data

---

_For more information about Claude's MCP capabilities, please refer to the [official documentation](https://modelcontextprotocol.io/introduction)_
