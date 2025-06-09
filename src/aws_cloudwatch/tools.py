import os
import logging
from enum import Enum
from typing import Optional
from contextlib import asynccontextmanager

import boto3
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context
from botocore.exceptions import ClientError, NoCredentialsError

from utils import (
    format_log_events,
    format_log_groups,
    format_log_streams
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")


DEFAULT_PAGE_SIZE = 10


class CloudWatchClientError(Exception):
    """
    Custom exception for CloudWatch client operations.

    This exception is raised when there are errors specific to CloudWatch
    operations, such as authentication failures or API errors.
    """


class LogStreamOrderChoices(Enum):
    """
    Enumeration for log stream ordering options.

    Attributes:
        LOG_STREAM_NAME: Order by log stream name alphabetically
        LAST_EVENT_TIME: Order by the time of the last event in the stream
    """
    LOG_STREAM_NAME = "LogStreamName"
    LAST_EVENT_TIME = "LastEventTime"

    @classmethod
    def validate(cls, value: str) -> str:
        """
        Validate the order by choice value against the enum.

        Args:
            value: The order by value to validate

        Returns:
            str: The validated order by value

        Raises:
            ValueError: If the orderby value is not valid
        """

        valid_choices = [choices.value for choices in cls]

        if value not in valid_choices:
            raise ValueError(
                f"Invalid order by value '{value}'. "
                f"Valid values are: {', '.join(valid_choices)}"
            )

        return value


@asynccontextmanager
async def lifespan(_: FastMCP):
    """
    Async context manager for managing CloudWatch client lifecycle.

    This function initializes the AWS CloudWatch client, tests the connection,
    and ensures proper cleanup when the server shuts down.

    Args:
        _: FastMCP instance (unused)

    Yields:
        boto3.client: Configured CloudWatch logs client

    Raises:
        CloudWatchClientError: If client initialization or connection fails
    """

    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY or not AWS_DEFAULT_REGION:
        raise CloudWatchClientError("AWS credentials are not configured")

    client = None
    try:
        client = boto3.client("logs")

        # Test the connection by attempting to list log groups
        client.list_log_groups(limit=1)
        logger.info("Successfully connected to AWS CloudWatch")

        yield client

    except NoCredentialsError as exc:
        raise CloudWatchClientError(
            "Invalid AWS credentials provided") from exc
    except ClientError as exc:
        raise CloudWatchClientError(f"AWS client error: {exc}") from exc
    except Exception as exc:
        raise CloudWatchClientError(
            f"Unexpected error initializing CloudWatch client: {exc}") from exc


# Initialize FastMCP server
mcp = FastMCP("aws_cw_logs", lifespan=lifespan)


@mcp.tool()
async def get_log_groups(
    ctx: Context,
    page_size: int = DEFAULT_PAGE_SIZE,
    next_page_token: Optional[str] = None
) -> str:
    """
    Retrieve a list of log groups from AWS CloudWatch.

    This function fetches log groups with pagination support. Each log group
    contains metadata such as creation time, retention policy, and storage size.

    Args:
        ctx: MCP context containing the CloudWatch client
        page_size: Maximum number of log groups to return (default: 10)
        next_page_token: Token for retrieving the next page of results

    Returns:
        str: Markdown-formatted string containing log groups data

    Raises:
        CloudWatchClientError: If there's an error fetching log groups
    """

    client = ctx.request_context.lifespan_context

    try:
        payload = {"limit": page_size}

        if next_page_token:
            payload["nextToken"] = next_page_token

        logger.info("Fetching log groups with page_size=%d", page_size)
        response = client.describe_log_groups(**payload)

        logger.info("Successfully retrieved %d log groups",
                    len(response.get('logGroups', [])))
        return format_log_groups(response)

    except ClientError as exc:
        error_msg = f"AWS error while fetching log groups: {exc}"
        logger.error(error_msg)
        raise CloudWatchClientError(error_msg) from exc

    except Exception as exc:
        error_msg = f"Unexpected error while fetching log groups: {exc}"
        logger.error(error_msg)
        raise CloudWatchClientError(error_msg) from exc


@mcp.tool()
async def get_log_streams(
    ctx: Context,
    log_group_name: str,
    page_size: int = DEFAULT_PAGE_SIZE,
    order_by: str = LogStreamOrderChoices.LAST_EVENT_TIME.value,
    next_page_token: Optional[str] = None
) -> str:
    """
    Get log streams for a specified log group.

    This function retrieves log streams within a log group, with options for
    pagination and ordering. Log streams represent individual sources of log
    events within a log group.

    Args:
        ctx: MCP context containing the CloudWatch client
        log_group_name: Name of the log group to retrieve streams for
        page_size: Maximum number of streams to return (default: 10)
        order_by: Sort order - 'LogStreamName' or 'LastEventTime' (default)
        next_page_token: Token for retrieving the next page of results

    Returns:
        str: Markdown-formatted string containing log streams data

    Raises:
        CloudWatchClientError: If there's an error fetching log streams
    """

    if not log_group_name or not isinstance(log_group_name, str):
        raise CloudWatchClientError(
            "log_group_name must be a non-empty string")

    LogStreamOrderChoices.validate(order_by)

    client = ctx.request_context.lifespan_context

    try:
        payload = {
            "logGroupName": log_group_name,
            "limit": page_size,
            "orderBy": order_by,
            "descending": True
        }

        if next_page_token:
            payload["nextToken"] = next_page_token

        logger.info("Fetching log streams for group '%s' with page_size=%d, order_by=%s",
                    log_group_name, page_size, order_by)
        response = client.describe_log_streams(**payload)

        logger.info("Successfully retrieved %d log streams",
                    len(response.get('logStreams', [])))
        return format_log_streams(response)

    except ClientError as exc:
        error_msg = f"AWS error while fetching log streams for '{log_group_name}': {exc}"
        logger.error(error_msg)
        raise CloudWatchClientError(error_msg) from exc

    except Exception as exc:
        error_msg = f"Unexpected error while fetching log streams for '{log_group_name}': {exc}"
        logger.error(error_msg)
        raise CloudWatchClientError(error_msg) from exc


@mcp.tool()
async def get_log_events(
    ctx: Context,
    log_group_name: str,
    log_stream_name: str,
    page_size: int = DEFAULT_PAGE_SIZE,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    next_page_token: Optional[str] = None
) -> str:
    """
    Get log events for a specified log group and stream.

    This function retrieves individual log events from a specific log stream,
    with support for time-based filtering and pagination. Each event contains
    a timestamp, message, and ingestion time.

    Args:
        ctx: MCP context containing the CloudWatch client
        log_group_name: Name of the log group
        log_stream_name: Name of the log stream
        page_size: Maximum number of events to return (default: 10)
        start_time: Start time in milliseconds since Unix epoch (inclusive)
        end_time: End time in milliseconds since Unix epoch (exclusive)
        next_page_token: Token for retrieving the next page of results

    Returns:
        str: Markdown-formatted string containing log events data

    Raises:
        CloudWatchClientError: If there's an error fetching log events
    """

    if not log_group_name or not isinstance(log_group_name, str):
        raise CloudWatchClientError(
            "log_group_name must be a non-empty string")

    if not log_stream_name or not isinstance(log_stream_name, str):
        raise CloudWatchClientError(
            "log_stream_name must be a non-empty string")

    client = ctx.request_context.lifespan_context

    try:
        payload = {
            "logGroupName": log_group_name,
            "logStreamName": log_stream_name,
            "limit": page_size
        }

        if start_time is not None:
            payload["startTime"] = start_time

        if end_time is not None:
            payload["endTime"] = end_time

        if next_page_token:
            payload["nextToken"] = next_page_token

        logger.info("Fetching log events for group '%s', stream '%s' with page_size=%d",
                    log_group_name, log_stream_name, page_size)
        response = client.get_log_events(**payload)

        logger.info("Successfully retrieved %d log events",
                    len(response.get('events', [])))
        return format_log_events(response)

    except ClientError as exc:
        error_msg = (f"AWS error while fetching log events for "
                     f"'{log_group_name}/{log_stream_name}': {exc}")
        logger.error(error_msg)
        raise CloudWatchClientError(error_msg) from exc

    except Exception as exc:
        error_msg = (f"Unexpected error while fetching log events for "
                     f"'{log_group_name}/{log_stream_name}': {exc}")
        logger.error(error_msg)
        raise CloudWatchClientError(error_msg) from exc
