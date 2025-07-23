import asyncio
from mcp_agent.core.fastagent import FastAgent

# Create the application
fast = FastAgent("aws-s3-mcp-client")

# Define the agent
@fast.agent(
    name="AWS S3 Agent",
    instruction="You are a helpful AI agent proficient in using AWS S3 resources to manage, store, and retrieve data efficiently.",
    servers=["aws-s3"]
)
async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        await agent.interactive()


if __name__ == "__main__":
    asyncio.run(main())