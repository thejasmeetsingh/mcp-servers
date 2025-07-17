import asyncio
from mcp_agent.core.fastagent import FastAgent

# Create the application
fast = FastAgent("web-search-mcp-client")

# Define the agent
@fast.agent(
    name="Web Search Agent",
    instruction="You are a helpful AI Agent",
    servers=["web-search"]
)
async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        await agent.interactive()


if __name__ == "__main__":
    asyncio.run(main())
