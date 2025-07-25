import asyncio
from mcp_agent.core.fastagent import FastAgent

# Create the application
fast = FastAgent("calendar-mcp-client")

# Define the agent
@fast.agent(
    name="Calendar Agent",
    instruction="You are a helpful AI Agent who manages user calendar.",
    servers=["calendar"]
)
async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        await agent.interactive()


if __name__ == "__main__":
    asyncio.run(main())