from typing import List, Dict, Any

import boto3


class S3Manager:
    def __init__(self, access_key: str, secret_key: str):
        self.client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
