#!/usr/bin/env python3

import boto3

from aws.s3_bucket import S3Bucket
from botocore.exceptions import ClientError
from pathlib import Path
from urllib.parse import urlparse


def download_folder(s3_uri, local_dir):
    """
    Download the contents of a folder directory
    Args:
        s3_uri: the s3 uri to the top level of the files you wish to download
        local_dir: a relative or absolute directory path in the local file system
    """
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(urlparse(s3_uri).hostname)
    s3_path = urlparse(s3_uri).path.lstrip("/")
    local_dir = Path(local_dir)
    for obj in bucket.objects.filter(Prefix=s3_path):
        target = local_dir / Path(obj.key).relative_to(s3_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        bucket.download_file(obj.key, str(target))


def download_file(s3_uri, local_dir, filename=None):
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(urlparse(s3_uri).hostname)
    key = urlparse(s3_uri).path.lstrip("/")
    filename = filename if filename is not None else key.split("/")[-1]
    target = Path(local_dir) / Path(filename)
    try:
        bucket.download_file(key, str(target))
    except Exception as e:
        if e.response["Error"]["Code"] == "404":
            print("The object does not exist.")
        else:
            raise


def upload_file(file_name, bucket, object_name):
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        return False
    return True


bucket_name = "artifact-bucket-stack-buildbucket-9omh0hnpg12q-copy"
prefix = "builds/1.1.0/15/x64/"
s3_uri = (
    "s3://artifact-bucket-stack-buildbucket-9omh0hnpg12q/builds/1.1.0/15/x64/maven/"
)
# s3_uri = 's3://artifact-bucket-stack-buildbucket-9omh0hnpg12q/builds/1.1.0/15/x64/'
s3_file_uri = "s3://artifact-bucket-stack-buildbucket-9omh0hnpg12q/builds/1.1.0/15/x64/bundle/opensearch-min-1.1.0-linux-x64.tar.gz"
s3 = boto3.resource("s3")
s3_client = boto3.client("s3")
local_dir = "/tmp/s3copy"

# for bucket in s3.buckets.all():
#     print(bucket.name)

client = boto3.client("s3")
# objects = client.list_objects_v2(Bucket=bucket_name)

# response = client.list_objects(Bucket=bucket_name, MaxKeys=2, Prefix=prefix)

# download_s3_folder(s3_file_uri, '/tmp/s3copy')
# download_file(s3_file_uri, '/tmp/s3copy')
# download_s3_folder(s3_uri, '/tmp/s3copy')
# upload_file('/tmp/s3copy/opensearch-min-1.1.0-linux-x64.tar.gz', bucket_name, 'tests/1.1.0/x64/opensearch-min-1.1.0-linux-x64.tar.gz')
# pprint(response)


# s3util = s3_utility.S3ReadWrite()

# s3util.download_file('s3://artifact-bucket-stack-buildbucket-9omh0hnpg12q/tests/1.1.0/x64/opensearch-min-1.1.0-linux-x64.tar.gz', local_dir)
# s3util.download_file(
#     "s3://artifact-bucket-stack-buildbucket-9omh0hnpg12q/bundles/1.1.0/16/arm64/opensearch-1.1.0-linux-arm64.tar.gz",
#     local_dir,
# )
# s3util.download_folder('s3://artifact-bucket-stack-buildbucket-9omh0hnpg12q/builds/1.1.0/15/x64/maven/', local_dir)
# s3util.upload_file('/tmp/s3copy/opensearch-min-1.1.0-linux-x64.tar.gz', bucket_name, 'tests/1.1.0/x64/opensearch-min-1.1.0-linux-x64.tar.gz')

# s3_utility.S3Bucket.download_file('artifact-bucket-stack-buildbucket-9omh0hnpg12q', 'bundles/1.1.0/16/arm64/opensearch-1.1.0-linux-arm64.tar.gz', local_dir)
# s3_utility.S3Bucket.download_folder('artifact-bucket-stack-buildbucket-9omh0hnpg12q', 'bundles/1.1.0/16/arm64/', local_dir)
# s3_utility.S3Bucket.upload_file('artifact-bucket-stack-buildbucket-9omh0hnpg12q', 'tests/opensearch-1.1.0-linux-arm64.tar.gz', local_dir + '/manifest.yml')
s3bucket = S3Bucket('artifact-bucket-stack-buildbucket-9omh0hnpg12q')
# s3bucket.download_file('bundles/1.1.0/16/arm64/opensearch-1.1.0-linux-arm64.tar.gz', local_dir)
s3bucket.download_folder('tests/', local_dir)