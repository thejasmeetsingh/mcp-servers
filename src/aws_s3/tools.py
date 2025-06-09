import os
import logging
import mimetypes
from enum import Enum
from typing import Optional
from contextlib import asynccontextmanager

import boto3
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context
from botocore.exceptions import ClientError, NoCredentialsError

from utils import (
    convert_dict_to_markdown,
    format_bucket_data,
    format_object_data,
    generate_unique_key
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Constants
DATA_DIRECTORY = "/data"


class S3ACL(Enum):
    """
    Enumeration of valid AWS S3 Access Control List (ACL) values.
    """

    PRIVATE = "private"
    PUBLIC_READ = "public-read"
    PUBLIC_READ_WRITE = "public-read-write"
    AUTHENTICATED_READ = "authenticated-read"
    AWS_EXEC_READ = "aws-exec-read"
    BUCKET_OWNER_READ = "bucket-owner-read"
    BUCKET_OWNER_FULL_CONTROL = "bucket-owner-full-control"

    @classmethod
    def validate(cls, acl_value: str) -> str:
        """
        Validate an ACL value against the enum.

        Args:
            acl_value: The ACL value to validate

        Returns:
            str: The validated ACL value

        Raises:
            ValueError: If the ACL value is not valid
        """

        valid_acls = [acl.value for acl in cls]

        if acl_value not in valid_acls:
            raise ValueError(
                f"Invalid ACL value '{acl_value}'. "
                f"Valid values are: {', '.join(valid_acls)}"
            )

        return acl_value

    @classmethod
    def get_valid_values(cls) -> list:
        """
        Get a list of all valid ACL values.

        Returns:
            list: List of valid ACL string values
        """

        return [acl.value for acl in cls]


class S3ClientError(Exception):
    """Custom exception for S3 client operations."""
    pass


@asynccontextmanager
async def lifespan(_: FastMCP):
    """
    Async context manager for managing the S3 client lifecycle.

    Validates AWS credentials and creates a boto3 S3 client that is
    properly closed after use.

    Args:
        _: FastMCP instance (unused)

    Yields:
        boto3.client: Configured S3 client

    Raises:
        S3ClientError: If AWS credentials are missing or invalid
    """

    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        raise S3ClientError("AWS credentials are not configured")

    client = None
    try:
        client = boto3.client("s3")

        # Test the connection by attempting to list buckets
        client.list_buckets()
        logger.info("Successfully connected to AWS S3")

        yield client

    except NoCredentialsError as exc:
        raise S3ClientError("Invalid AWS credentials provided") from exc
    except ClientError as exc:
        raise S3ClientError(f"AWS client error: {exc}") from exc
    except Exception as exc:
        raise S3ClientError(
            f"Unexpected error initializing S3 client: {exc}") from exc
    finally:
        if client:
            client.close()
            logger.info("S3 client connection closed")


# Initialize FastMCP server
mcp = FastMCP("aws_s3", lifespan=lifespan)


@mcp.tool()
async def get_buckets(ctx: Context, next_page_token: Optional[str] = None) -> str:
    """
    Retrieve list of S3 buckets.

    Args:
        ctx: FastMCP context containing the S3 client
        next_page_token: Token for pagination (optional)

    Returns:
        str: Markdown formatted list of buckets

    Raises:
        S3ClientError: If there's an error fetching buckets
    """

    try:
        client = ctx.request_context.lifespan_context
        kwargs = {}

        if next_page_token:
            kwargs["ContinuationToken"] = next_page_token

        response = client.list_buckets(**kwargs)
        buckets = response.get("Buckets", [])

        if not buckets:
            return "No buckets found."

        formatted_buckets = format_bucket_data(buckets)

        result_data = {
            "buckets": formatted_buckets,
            "next_page_token": response.get("ContinuationToken", "")
        }

        logger.info("Successfully retrieved %d buckets", len(buckets))
        return convert_dict_to_markdown(result_data)

    except ClientError as exc:
        error_msg = f"AWS error while fetching buckets: {exc}"
        logger.error(error_msg)
        raise S3ClientError(error_msg) from exc

    except Exception as exc:
        error_msg = f"Unexpected error while fetching buckets: {exc}"
        logger.error(error_msg)
        raise S3ClientError(error_msg) from exc


@mcp.tool()
async def get_bucket_objects(
    ctx: Context,
    bucket: str,
    next_page_token: Optional[str] = None
) -> str:
    """
    Retrieve list of objects in a specific S3 bucket.

    Args:
        ctx: FastMCP context containing the S3 client
        bucket: Name of the S3 bucket
        next_page_token: Token for pagination (optional)

    Returns:
        str: Markdown formatted list of objects

    Raises:
        S3ClientError: If there's an error fetching bucket objects
    """

    try:
        client = ctx.request_context.lifespan_context
        kwargs = {"Bucket": bucket}

        if next_page_token:
            kwargs["ContinuationToken"] = next_page_token

        response = client.list_objects_v2(**kwargs)
        objects = response.get("Contents", [])

        if not objects:
            return f"No objects found in bucket '{bucket}'."

        formatted_objects = format_object_data(objects)

        result_data = {
            "bucket": bucket,
            "objects": formatted_objects,
            "next_page_token": response.get("ContinuationToken", "")
        }

        logger.info("Successfully retrieved %d objects from bucket '%s'",
                    len(objects), bucket)

        return convert_dict_to_markdown(result_data)

    except ClientError as exc:
        error_msg = f"AWS error while fetching objects from bucket '{bucket}': {exc}"
        logger.error(error_msg)
        raise S3ClientError(error_msg) from exc

    except Exception as exc:
        error_msg = f"Unexpected error while fetching bucket objects: {exc}"
        logger.error(error_msg)
        raise S3ClientError(error_msg) from exc


@mcp.tool()
async def upload_file(
    ctx: Context,
    bucket: str,
    filename: str,
    acl: str = S3ACL.PRIVATE.value
) -> str:
    """
    Upload a file to an S3 bucket.

    Args:
        ctx: FastMCP context containing the S3 client
        bucket: Name of the target S3 bucket
        filename: Name of the file to upload (must exist in /data directory)
        acl: Access control list setting. Valid values are:
            - 'private': Owner gets full control. No one else has access rights.
            - 'public-read': Owner gets full control. All users get read access.
            - 'public-read-write': Owner gets full control. All users get read and write access.
            - 'authenticated-read': Owner gets full control. Authenticated users get read access.
            - 'aws-exec-read': Owner gets full control. AWS services get read access for execution.
            - 'bucket-owner-read': Object owner gets full control. Bucket owner gets read access.
            - 'bucket-owner-full-control': Both object owner and bucket owner get full control.
            Default: 'private'

    Returns:
        str: Success message with bucket name and generated key

    Raises:
        S3ClientError: If file doesn't exist or upload fails
        ValueError: If ACL value is invalid
    """

    try:
        # Validate ACL value
        validated_acl = S3ACL.validate(acl)

        file_path = os.path.join(DATA_DIRECTORY, filename)

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File '{filename}' does not exist")

        client = ctx.request_context.lifespan_context
        content_type, _ = mimetypes.guess_type(file_path)

        # Use default content type if not detected
        if not content_type:
            content_type = "application/octet-stream"

        key = generate_unique_key(file_path)

        with open(file_path, "rb") as fp:
            client.put_object(
                ACL=validated_acl,
                Bucket=bucket,
                ContentType=content_type,
                Body=fp,
                Key=key
            )

        success_msg = (
            f"File '{filename}' uploaded successfully to bucket '{bucket}' "
            f"with key '{key}' and ACL '{validated_acl}'"
        )
        logger.info(success_msg)
        return success_msg

    except ValueError as exc:
        # Re-raise ValueError for ACL validation errors
        logger.error("ACL validation error: %s", exc)
        raise

    except ClientError as exc:
        error_msg = f"AWS error while uploading file '{filename}': {exc}"
        logger.error(error_msg)
        raise S3ClientError(error_msg) from exc

    except OSError as exc:
        error_msg = f"File system error while uploading '{filename}': {exc}"
        logger.error(error_msg)
        raise S3ClientError(error_msg) from exc

    except Exception as exc:
        error_msg = f"Unexpected error while uploading file '{filename}': {exc}"
        logger.error(error_msg)
        raise S3ClientError(error_msg) from exc


@mcp.tool()
async def delete_file(ctx: Context, bucket: str, key: str) -> str:
    """
    Delete a file from an S3 bucket.

    Args:
        ctx: FastMCP context containing the S3 client
        bucket: Name of the S3 bucket
        key: S3 key of the file to delete

    Returns:
        str: Success message confirming deletion

    Raises:
        S3ClientError: If deletion fails
    """

    try:
        client = ctx.request_context.lifespan_context
        client.delete_object(Bucket=bucket, Key=key)

        success_msg = f"File with key '{key}' deleted successfully from bucket '{bucket}'"
        logger.info(success_msg)
        return success_msg

    except ClientError as exc:
        error_msg = f"AWS error while deleting file '{key}' from bucket '{bucket}': {exc}"
        logger.error(error_msg)
        raise S3ClientError(error_msg) from exc

    except Exception as exc:
        error_msg = f"Unexpected error while deleting file '{key}': {exc}"
        logger.error(error_msg)
        raise S3ClientError(error_msg) from exc


@mcp.tool()
async def download_file(ctx: Context, bucket: str, key: str) -> str:
    """
    Download a file from an S3 bucket to the local data directory.

    Args:
        ctx: FastMCP context containing the S3 client
        bucket: Name of the S3 bucket
        key: S3 key of the file to download

    Returns:
        str: Success message with downloaded file path

    Raises:
        S3ClientError: If download fails
    """

    try:
        filename = os.path.basename(key)
        file_path = os.path.join(DATA_DIRECTORY, filename)

        client = ctx.request_context.lifespan_context

        with open(file_path, "wb") as file_handle:
            client.download_fileobj(bucket, key, file_handle)

        success_msg = f"File '{key}' downloaded successfully from bucket '{bucket}'."
        logger.info(success_msg)
        return success_msg

    except ClientError as exc:
        error_msg = f"AWS error while downloading file '{key}' from bucket '{bucket}': {exc}"
        logger.error(error_msg)
        raise S3ClientError(error_msg) from exc
    except OSError as exc:
        error_msg = f"File system error while downloading '{key}': {exc}"
        logger.error(error_msg)
        raise S3ClientError(error_msg) from exc
    except Exception as exc:
        error_msg = f"Unexpected error while downloading file '{key}': {exc}"
        logger.error(error_msg)
        raise S3ClientError(error_msg) from exc
