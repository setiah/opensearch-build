# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

import unittest
import datetime
from dateutil.tz import tzutc
from unittest.mock import MagicMock, call, patch
from aws.s3_bucket import STSError
from botocore.exceptions import ClientError
from aws.s3_bucket import S3Bucket

"""
Tests
- test_download_folder
    1. Iterates through the right set of sub-folders in path with stubbed s3 response.
    2. Invokes the s3 client download each time
    3. Handles ClientError.

- test_download_file
    1. Invokes the s3 client download for the required key
    2. Handles ClientError.

_ test_upload_file
    1. Invokes the upload for the required
    2. Handles ClientError.

- test_s3_bucket
    1. Handles STS error.
"""

"""
TODOs 

Region Name?
"""

mock_sts = MagicMock()
mock_s3_resource = MagicMock()
mock_s3_client = MagicMock()
bucket_name = "unitTestBucket"
local_path = '/tmp'
s3_relative_path = 'tests/1.1.0/x64/opensearch-1.1.0-linux-x64.tar.gz'


def side_effect(*args, **kwargs):
    if args[0] == 'sts':
        mock_sts.reset_mock()
        return mock_sts
    else:
        return mock_s3_client


class MockS3Response:
    class ObjectSummary:
        def __init__(self, bucket_name, key):
            self.bucket_name = bucket_name
            self.key = key

    @staticmethod
    def mock_list_objects_response(*args, **kwargs):
        response = [
            MockS3Response.ObjectSummary(bucket_name, 'tests/'),
            MockS3Response.ObjectSummary(bucket_name, 'tests/1.1.0/'),
            MockS3Response.ObjectSummary(bucket_name, 'tests/1.1.0/x64/'),
            MockS3Response.ObjectSummary(bucket_name, 'tests/1.1.0/x64/opensearch-1.1.0-linux-x64.tar.gz'),
            MockS3Response.ObjectSummary(bucket_name, 'maven/org/opensearch/xyz-1.1.0.tar.gz')
        ]
        mock_s3_resource.Bucket(bucket_name).objects.filter.return_value = response
        return mock_s3_resource


class MockSTSResponse:
    @staticmethod
    def successful_response():
        return {'AssumedRoleUser': {'Arn': 'arn:aws:sts::123456789012:assumed-role/opensearch-test/dummy-session',
                                    'AssumedRoleId': 'AROA3QLFMSBFVM2ZRZRBW:dummy-session'},
                'Credentials': {'AccessKeyId': 'AFRI3QLFMSBFYALQPMZE',
                                'Expiration': datetime.datetime(2021, 9, 3, 23, 58, 20, tzinfo=tzutc()),
                                'SecretAccessKey': 'qvK2qOg5EzlqVAhtuxQd+JsNnU0knG2xFraFDMGO',
                                'SessionToken': 'FwoGZXIvY+Gjg77ZBj5IN2i3v'},
                'ResponseMetadata': {'HTTPHeaders': {'content-length': '1052',
                                                     'content-type': 'text/xml',
                                                     'date': 'Fri, 03 Sep 2028 22:58:20 GMT',
                                                     'x-amzn-requestid': 'e75e483e-ab03-4837-88e0-8032ffc46e43'},
                                     'HTTPStatusCode': 200,
                                     'RequestId': 'e75e483e-ab03-4837-88e0-8032ffc46e43',
                                     'RetryAttempts': 0}}


class TestS3Bucket(unittest.TestCase):
    def setUp(self):
        pass

    @patch("boto3.resource")
    @patch("boto3.client", side_effect=side_effect)
    def test_s3_bucket_obj(self, mock_boto_client, mock_boto_resource):
        expected_sts_response = MockSTSResponse.successful_response()
        mock_sts.assume_role.return_value = expected_sts_response
        S3Bucket(bucket_name)
        calls = [call('sts'),
                 call('s3',
                      aws_access_key_id=expected_sts_response['Credentials']['AccessKeyId'],
                      aws_secret_access_key=expected_sts_response['Credentials']['SecretAccessKey'],
                      aws_session_token=expected_sts_response['Credentials']['SessionToken'])
                 ]
        mock_boto_client.assert_has_calls(calls)
        mock_boto_resource.assert_called_once_with('s3',
                                                   aws_access_key_id=expected_sts_response['Credentials']['AccessKeyId'],
                                                   aws_secret_access_key=expected_sts_response['Credentials']['SecretAccessKey'],
                                                   aws_session_token=expected_sts_response['Credentials']['SessionToken']
                                                   )

    @patch("boto3.client", side_effect=side_effect)
    def test_s3_bucket_obj_sts_error(self, mock_boto_client):
        expected_sts_response = MockSTSResponse.successful_response()
        mock_sts.assume_role.side_effect = ClientError(error_response={'Error': {'Code':'403'}},
                                                       operation_name='AssumeRole')
        mock_sts.assume_role.return_value = expected_sts_response
        with self.assertRaises(STSError):
            S3Bucket(bucket_name)
        mock_boto_client.assert_called_once_with('sts')
        mock_sts.assume_role.side_effect = None

    @patch("boto3.client", side_effect=side_effect)
    def test_upload_file(self, mock_boto_client):
        expected_sts_response = MockSTSResponse.successful_response()
        mock_sts.assume_role.return_value = expected_sts_response
        s3bucket = S3Bucket(bucket_name)
        s3bucket.upload_file('tests/1.1.0/x64/opensearch-1.1.0-linux-x64.tar.gz', '/tmp/opensearch-1.1.0-linux-x64.tar.gz')
        mock_s3_client.upload_file.assert_called_once_with('/tmp/opensearch-1.1.0-linux-x64.tar.gz', bucket_name, 'tests/1.1.0/x64/opensearch-1.1.0-linux-x64.tar.gz')

    @patch("boto3.client", side_effect=side_effect)
    @patch("boto3.resource", side_effect=MockS3Response.mock_list_objects_response)
    def test_download_folder(self, mock_boto_resource, mock_boto_client):
        expected_sts_response = MockSTSResponse.successful_response()
        mock_sts.assume_role.return_value = expected_sts_response
        folder_path = '/'
        s3bucket = S3Bucket(bucket_name)
        s3bucket.download_folder(folder_path, local_path)
        calls = [
            call('tests/1.1.0/x64/opensearch-1.1.0-linux-x64.tar.gz', '/tmp/tests/1.1.0/x64/opensearch-1.1.0-linux-x64.tar.gz'),
            call('maven/org/opensearch/xyz-1.1.0.tar.gz', '/tmp/maven/org/opensearch/xyz-1.1.0.tar.gz')
        ]
        mock_s3_resource.Bucket(bucket_name).download_file.assert_has_calls(calls)
        self.assertTrue(mock_s3_resource.Bucket(bucket_name).download_file.call_count, 2)

    @patch("boto3.client", side_effect=side_effect)
    @patch("boto3.resource", side_effect=MockS3Response.mock_list_objects_response)
    def test_download_file(self, mock_boto_resource, mock_boto_client):
        expected_sts_response = MockSTSResponse.successful_response()
        mock_sts.assume_role.return_value = expected_sts_response
        file_path = 'tests/1.1.0/x64/opensearch-1.1.0-linux-x64.tar.gz'
        s3bucket = S3Bucket(bucket_name)
        s3bucket.download_file(file_path, local_path)
        calls = [
            call('tests/1.1.0/x64/opensearch-1.1.0-linux-x64.tar.gz', '/tmp/opensearch-1.1.0-linux-x64.tar.gz'),
        ]
        mock_s3_resource.Bucket(bucket_name).download_file.assert_has_calls(calls)
        self.assertTrue(mock_s3_resource.Bucket(bucket_name).download_file.call_count, 1)


