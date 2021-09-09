# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

import itertools
import logging
import os
import subprocess
import time
import urllib.request

import requests

from paths.tree_walker import walk
from test_workflow.test_cluster import ClusterCreationException, TestCluster
from aws.s3_bucket import S3Bucket


class LocalTestCluster(TestCluster):
    """
    Represents an on-box test cluster. This class downloads a bundle (from a BundleManifest) and runs it as a background process.
    """

    def __init__(self, work_dir, bundle_manifest, security_enabled, s3_bucket):
        self.s3_bucket = s3_bucket
        self.manifest = bundle_manifest
        self.work_dir = os.path.join(work_dir, "local-test-cluster")
        os.makedirs(self.work_dir, exist_ok=True)
        self.security_enabled = security_enabled
        self.process = None

    def create(self):
        self.download()
        self.stdout = open("stdout.txt", "w")
        self.stderr = open("stderr.txt", "w")
        self.install_dir = f"opensearch-{self.manifest.build.version}"
        if not self.security_enabled:
            self.disable_security(self.install_dir)
        self.process = subprocess.Popen(
            "./opensearch-tar-install.sh",
            cwd=self.install_dir,
            shell=True,
            stdout=self.stdout,
            stderr=self.stderr,
        )
        logging.info(f"Started OpenSearch with PID {self.process.pid}")
        self.wait_for_service()

    def endpoint(self):
        return "localhost"

    def port(self):
        return 9200

    def destroy(self):
        if self.process is None:
            logging.info("Local test cluster is not started")
            return
        self.terminate_process()
        # test_recorder.record_cluster_logs(
        #     itertools.chain(
        #         [
        #             (os.path.realpath(self.stdout.name), "stdout"),
        #             (os.path.realpath(self.stderr.name), "stderr"),
        #         ],
        #         walk(os.path.join(self.install_dir, "logs")),
        #     )
        # )

    def url(self, path=""):
        return f'{"https" if self.security_enabled else "http"}://{self.endpoint()}:{self.port()}{path}'

    def download(self):
        s3bucket = S3Bucket(self.s3_bucket)
        logging.info(f"Creating local test cluster in {self.work_dir}")
        os.chdir(self.work_dir)
        logging.info(f"Downloading bundle from {self.manifest.build.location}")
        parsed_url = urllib.parse.urlparse(self.manifest.build.location)
        s3bucket.download_file(parsed_url.path.lstrip('/'), self.work_dir)
        bundle_name = parsed_url.path.split('/')[-1]
        # urllib.request.urlretrieve(self.manifest.build.location, "bundle.tgz")
        logging.info(f'Downloaded bundle to {os.path.realpath(bundle_name)}')
        logging.info("Unpacking")
        subprocess.check_call(f"tar -xzf {bundle_name}", shell=True)
        logging.info("Unpacked")

    def disable_security(self, dir):
        subprocess.check_call(
            f'echo "plugins.security.disabled: true" >> {os.path.join(dir, "config", "opensearch.yml")}',
            shell=True,
        )

    def wait_for_service(self):
        logging.info("Waiting for service to become available")
        url = self.url("/_cluster/health")

        for attempt in range(10):
            try:
                logging.info(f"Pinging {url} attempt {attempt}")
                response = requests.get(url, verify=False, auth=("admin", "admin"))
                logging.info(f"{response.status_code}: {response.text}")
                if response.status_code == 200 and '"status":"green"' in response.text:
                    logging.info("Cluster is green")
                    return
            except requests.exceptions.ConnectionError:
                logging.info("Service not available yet")
            time.sleep(10)
        raise ClusterCreationException("Cluster is not green after 10 attempts")

    def terminate_process(self):
        logging.info(f"Sending SIGTERM to PID {self.process.pid}")
        self.process.terminate()
        try:
            logging.info("Waiting for process to terminate")
            self.process.wait(10)
        except subprocess.TimeoutExpired:
            logging.info("Process did not terminate after 10 seconds. Sending SIGKILL")
            self.process.kill()
            try:
                logging.info("Waiting for process to terminate")
                self.process.wait(10)
            except subprocess.TimeoutExpired:
                logging.info("Process failed to terminate even after SIGKILL")
                raise
        finally:
            logging.info(f"Process terminated with exit code {self.process.returncode}")
            self.stdout.close()
            self.stderr.close()
            self.process = None
