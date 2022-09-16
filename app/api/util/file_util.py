import os
from pathlib import PosixPath
from typing import Optional, Tuple
from urllib.parse import urlparse

import boto3
import botocore

##################################
# Path parsing utils
##################################


def is_s3_path(path: str | PosixPath) -> bool:
    return str(path).startswith("s3://")


def split_s3_url(path: str) -> Tuple[str, str]:
    parts = urlparse(path)
    bucket_name = parts.netloc
    prefix = parts.path.lstrip("/")
    return (bucket_name, prefix)


def get_s3_bucket(path: str) -> Optional[str]:
    return urlparse(path).hostname


def get_s3_file_key(path: str) -> str:
    return urlparse(path).path[1:]


def get_file_name(path: str) -> str:
    return os.path.basename(path)


##################################
# S3 Utilities
##################################


def get_s3_client(boto_session: Optional[boto3.Session] = None) -> botocore.client.BaseClient:
    """Returns an S3 client, wrapping around boiler plate if you already have a session"""
    if boto_session:
        return boto_session.client("s3")

    return boto3.client("s3")


##################################
# File operation utils
##################################


def list_files(
    path: str, recursive: bool = False, boto_session: Optional[boto3.Session] = None
) -> list[str]:
    """List the immediate files under path.

    There is minor inconsistency between local path handling and S3 paths.
    Directory names will be included for local paths, whereas they will not for
    S3 paths.

    Args:
        path: Supports s3:// and local paths.
        recursive: Only applicable for S3 paths.
            If set to True will recursively list all relative key paths under the prefix.
        boto_session: Boto session object to use for S3 access. Only necessary
            if needing to access an S3 bucket with assumed credentials (e.g.,
            cross-account bucket access).
    """
    if is_s3_path(path):
        bucket_name, prefix = split_s3_url(path)

        # in order for s3.list_objects to only list the immediate "files" under
        # the given path, the prefix should end in the path delimiter
        if prefix and not prefix.endswith("/"):
            prefix = prefix + "/"

        s3 = get_s3_client(boto_session)

        # When the delimiter is provided, s3 knows to stop listing keys that contain it (starting after the prefix).
        # https://docs.aws.amazon.com/AmazonS3/latest/dev/ListingKeysHierarchy.html
        delimiter = "" if recursive else "/"

        paginator = s3.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter=delimiter)

        file_paths = []
        for page in pages:
            object_contents = page.get("Contents")

            if object_contents:
                for object in object_contents:
                    if recursive:
                        key = object["Key"]
                        start_index = key.index(prefix) + len(prefix)
                        file_paths.append(key[start_index:])
                    else:
                        file_paths.append(get_file_name(object["Key"]))

        return file_paths

    # os.listdir throws an exception if the path doesn't exist
    # Make it behave like S3 list and return an empty list
    if os.path.exists(path):
        return os.listdir(path)
    return []
