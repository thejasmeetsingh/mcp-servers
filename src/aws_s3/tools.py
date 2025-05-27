import os
import logging

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from utils import convert_dict_to_markdown


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
