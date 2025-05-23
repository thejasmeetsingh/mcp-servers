# Google Maps MCP Server

A powerful Model Context Protocol (MCP) server that brings Google Maps functionality directly to Claude Desktop. Transform your AI assistant into a location-aware helper capable of finding places, planning routes, checking weather, and monitoring air quality.

## 🌟 What You Can Do

Transform Claude into your personal navigation and location assistant:

- **🗺️ Address & Location Services**: Convert addresses to coordinates and vice versa
- **🔍 Smart Place Discovery**: Find restaurants, hotels, attractions, and services with intelligent search
- **🛣️ Intelligent Route Planning**: Get optimized directions for driving, walking, cycling, or public transit
- **🌤️ Weather Intelligence**: Access detailed forecasts up to 14 days ahead
- **🌬️ Air Quality Monitoring**: Real-time air quality data with health recommendations
- **💬 Natural Language Interface**: Ask questions like "Find Italian restaurants near Central Park" or "What's the weather like in Tokyo next week?"

## 🎯 Real-World Use Cases

**Travel & Tourism**

- Plan multi-stop itineraries with optimal routing
- Discover local attractions and hidden gems
- Check weather conditions before outdoor activities
- Monitor air quality for health-conscious travel

**Daily Life**

- Find the nearest coffee shop or gas station
- Compare route options during rush hour
- Plan outdoor activities around weather forecasts
- Make informed decisions about air quality for exercise

**Business & Work**

- Scout locations for meetings or events
- Plan delivery routes and logistics
- Research competitor locations
- Analyze weather impact on business operations

## 📋 Prerequisites

Before getting started, ensure you have:

- **Docker**: Installed and running on your system ([Download Docker](https://docs.docker.com/get-docker/))
- **Claude Desktop**: The official Claude desktop application ([Download Claude](https://claude.ai/download))
- **Google Cloud Project**: Set up with billing enabled ([Setup Guide](https://developers.google.com/maps/documentation/javascript/cloud-setup))

### 🔑 Google Cloud Setup (Step-by-Step)

1. **Create a Google Cloud Project**

   - Visit the [Google Cloud Console](https://console.cloud.google.com/)
   - Click "New Project" and give it a descriptive name
   - Enable billing for your project

2. **Generate an API Key**

   - Navigate to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "API Key"
   - Copy your API key securely ([Detailed Guide](https://developers.google.com/maps/documentation/javascript/get-api-key#create-api-keys))

3. **Enable Required APIs**
   Navigate to "APIs & Services" → "Library" and enable these APIs:

   - ✅ **Air Quality API** - For pollution and air quality data
   - ✅ **Geocoding API** - For address-to-coordinates conversion
   - ✅ **Places API (New)** - For location search and discovery
   - ✅ **Routes API** - For navigation and route planning
   - ✅ **Weather API** - For weather forecasts and conditions

4. **Secure Your API Key (Recommended)**
   - In "Credentials", click on your API key
   - Add application restrictions (IP addresses or HTTP referrers)
   - Restrict to only the APIs listed above

## 🚀 Installation & Setup

### Step 1: Build the Docker Container

```bash
# Clone the repository
git clone https://github.com/thejasmeetsingh/mcp-servers.git

# Navigate to the Google Maps MCP directory
cd src/google-maps/

# Build the Docker image
docker build -t mcp/google-maps .
```

### Step 2: Configure Claude Desktop

Locate your Claude Desktop configuration file:

**Configuration File Locations:**

- 🪟 **Windows**: `%APPDATA%\Claude Desktop\claude_desktop_config.json`
- 🍎 **macOS**: `~/Library/Application Support/Claude Desktop/claude_desktop_config.json`
- 🐧 **Linux**: `~/.config/Claude Desktop/claude_desktop_config.json`

**Add this configuration** (replace `<YOUR_API_KEY>` with your actual Google Cloud API key):

```json
{
  "mcpServers": {
    "google-maps": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "API_KEY=<YOUR_API_KEY>",
        "--name",
        "google-maps",
        "mcp/google-maps"
      ]
    }
  }
}
```

### Step 3: Launch Claude Desktop

1. **Save** your configuration file
2. **Completely restart** Claude Desktop (quit and reopen)
3. **Verify connection** by asking Claude: "Can you search for coffee shops in manhattan center?"

## 💡 Example Conversations

Once configured, try these natural language queries:

**🍕 Finding Places**

- "Find the best pizza places in Brooklyn"
- "What are some highly-rated museums near the Louvre in Paris?"
- "Show me gas stations within 5 miles of downtown Seattle"

**🗺️ Route Planning**

- "What's the fastest route from LAX to Hollywood Boulevard right now?"
- "Plan a walking route from Central Park to Times Square"
- "Compare driving vs public transit from Brooklyn Bridge to Staten Island"

**🌦️ Weather Planning**

- "What's the weather forecast for my trip to London next week?"
- "Will it rain in San Francisco this weekend?"
- "Show me the 5-day weather forecast for Tokyo"

**🌬️ Air Quality Monitoring**

- "What's the air quality like in Beijing today?"
- "Is it safe to exercise outdoors in Los Angeles right now?"
- "Check air quality conditions in New Delhi for the next few hours"

**🔄 Combined Queries**

- "Find outdoor restaurants in Miami and check if the weather is good for dining outside tonight"
- "Plan a route to Central Park and let me know if the air quality is safe for jogging"

## 🛠️ Troubleshooting

### Common Issues and Solutions

**🐳 Docker Problems**

```bash
# Check if Docker is running
docker --version

# Test container manually
docker run -e "API_KEY=your_key_here" mcp/google-maps

# View container logs
docker container logs google-maps
```

**🔐 Authentication Issues**

- Verify your API key is correctly set in the configuration
- Ensure all required APIs are enabled in Google Cloud Console
- Check that your Google Cloud project has billing enabled
- Confirm API key restrictions aren't blocking requests

**⚙️ Configuration Problems**

- Validate JSON syntax using an online JSON validator
- Ensure file path is correct for your operating system
- Try removing and re-adding the configuration
- Restart Claude Desktop completely after changes

**📱 Connection Issues**

- Check your internet connection
- Verify Docker container has network access
- Ensure firewall isn't blocking Docker containers
- Try rebuilding the Docker image

### Getting Help

If issues persist:

1. Check the container logs: `docker container logs google-maps`
2. Verify API quotas in Google Cloud Console
3. Test your API key with a simple HTTP request
4. Review Claude Desktop's debug logs (if available)

## 🔒 Security & Privacy

**Your Data Protection**

- API keys are stored locally in your configuration file
- No data is transmitted beyond Google's official APIs
- The MCP server runs in an isolated Docker container
- All communication happens locally between Claude and the container

**Best Practices**

- Regularly rotate your Google Cloud API keys
- Set up API key restrictions in Google Cloud Console
- Monitor API usage to detect unusual activity
- Keep your Docker images updated

## 📈 Usage Monitoring

Keep track of your Google Cloud API usage:

- Visit [Google Cloud Console](https://console.cloud.google.com/) → "APIs & Services" → "Quotas"
- Monitor daily/monthly API call limits
- Set up billing alerts to avoid unexpected charges
- Review usage patterns to optimize your queries

---

_For more information about Model Context Protocol, visit the [official MCP documentation](https://modelcontextprotocol.io/introduction)_
