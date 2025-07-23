import asyncio
from mcp_agent.core.fastagent import FastAgent

# Create the application
fast = FastAgent("aws-cloudwatch-mcp-client")

# Define the agent
@fast.agent(
    name="AWS CloudWatch Agent",
    instruction="You are a helpful AI agent proficient in using AWS CloudWatch to monitor, log, and analyze system performance and application metrics.",
    servers=["aws-cloudwatch"]
)
async def main():
    # use the --model command line switch or agent arguments to change model
    async with fast.run() as agent:
        await agent.interactive()


if __name__ == "__main__":
    asyncio.run(main())