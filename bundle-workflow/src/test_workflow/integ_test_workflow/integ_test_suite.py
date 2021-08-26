# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

import os


class IntegTestSuite:
    def __init__(self, component, bundle_manifest, script_finder):
        self.name = component.name
        self.repo = component.repository
        self.bundle_manifest = bundle_manifest
        self.script_finder = script_finder

    def run_component_integ_tests(self, component, work_dir):
        try:
            # Spin up a test cluster
            cluster = LocalTestCluster(self.bundle_manifest, work_dir)
            cluster.create()
            print("component name: " + component.name)
            # TODO: (Create issue) Since plugins don't have integtest.sh in version branch, hardcoded it to main
            # repo = GitRepository(component.repository, component.commit_id, os.path.join(work_dir, component.name))
            repo = GitRepository(component.repository, 'main', os.path.join(work_dir, component.name))
            test_suite = IntegTestSuite(component.name, repo)
            test_suite.execute(cluster)
        finally:
            cluster.destroy()


    def execute(self, cluster, security):
        script = self.script_finder.find_integ_test_script(self.name, self.repo.dir)
        if os.path.exists(script):
            self.repo.execute(
                f"{script} -b {cluster.endpoint()} -p {cluster.port()} -s {str(security).lower()}"
            )
        else:
            print(f"{script} does not exist. Skipping integ tests for {self.name}")
