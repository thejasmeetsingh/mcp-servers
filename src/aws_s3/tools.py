import os
import logging
import datetime
import mimetypes
from contextlib import asynccontextmanager

import boto3
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context

from utils import convert_dict_to_markdown


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
ACCESS_KEY_ID = os.getenv("ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.getenv("SECRET_ACCESS_KEY")


@asynccontextmanager
async def lifespan(_: FastMCP):
    if not ACCESS_KEY_ID or not SECRET_ACCESS_KEY:
            raise ValueError("AWS credentials is not configured")

    try:
        client = boto3.client(
            "s3",
            aws_access_key_id=ACCESS_KEY_ID,
            aws_secret_access_key=SECRET_ACCESS_KEY
        )
        yield client

    except Exception as e:
        logger.error(str(e))
        raise ValueError(e) from e
    
    finally:
        client.close()


mcp = FastMCP("aws_s3", lifespan=lifespan)

mcp.prompt()


@mcp.tool()
async def get_buckets(ctx: Context, next_page_token: str = None) -> str:
    try:
        client = ctx.request_context.lifespan_context

        kwargs = {}

        if next_page_token:
            kwargs["ContinuationToken"] = next_page_token

        response = client.list_buckets(**kwargs)

        buckets = response.get("Buckets", [])
        if not buckets:
            return "No buckets found."

        logger.info(f"Successfully retreived {len(buckets)} buckets.")

        buckets = [{
            "name": bucket["Name"],
            "created_at": bucket["CreationDate"].isoformat()
        } for bucket in buckets]

        return convert_dict_to_markdown({
            "buckets": buckets,
            "next_page_token": response.get("ContinuationToken", "")
        })

    except Exception as e:
        raise ValueError(f"Error caught while fetching buckets from S3: {str(e)}") from e


@mcp.tool()
async def get_bucket_objects(ctx: Context, bucket: str, next_page_token: str = "") -> str:
    try:
        client = ctx.request_context.lifespan_context
        kwargs = {"Bucket": bucket}

        if next_page_token:
            kwargs["ContinuationToken"] = next_page_token

        response = client.list_objects_v2(**kwargs)

        objects = response.get("Contents", [])
        if not objects:
            return "No objects found."

        logger.info(f"Successfully retreived {len(objects)} objects.")

        objects = [{
            "key": _object["Key"],
            "modified_at": _object["LastModified"].isoformat(),
            "size (in bytes)": _object["Size"]
        } for _object in objects]

        return convert_dict_to_markdown({
            "objects": objects,
            "next_page_token": response.get("ContinuationToken", "")
        })

    except Exception as e:
        raise ValueError(f"Error caught while fetching buckets objects: {str(e)}") from e


@mcp.tool()
async def upload_file(ctx: Context, acl: str, bucket: str, file_path: str) -> str:
    try:
        if not os.path.isfile(file_path):
            raise ValueError("File on the given path does not exists.")

        client = ctx.request_context.lifespan_context

        content_type = mimetypes.guess_type(file_path)[0]
        key = f"{os.path.basename(file_path)}-{round(datetime.datetime.now().timestamp())}"

        with open(file_path, "rb") as fp:
            client.put_object(ACL=acl, Bucket=bucket, ContentType=content_type, Body=fp, Key=key)

        return f"Given file is uploaded to {bucket} bucket successfully"

    except Exception as e:
        raise ValueError(f"Error caught while uploading a file: {str(e)}") from e



@mcp.tool()
async def delete_file(ctx: Context, bucket: str, key: str) -> str:
    try:
        client = ctx.request_context.lifespan_context
        client.delete_object(Bucket=bucket, Key=key)

        return f"File with the key: {key} in bucket: {bucket} is deleted successfully"
    except Exception as e:
        raise ValueError(f"Error caught while deleting a file: {str(e)}") from e
