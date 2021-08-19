#!/usr/bin/env python

import argparse
import os
import sys

from manifests.bundle_manifest import BundleManifest
from git.git_repository import GitRepository
from test_workflow.test_cluster import LocalTestCluster
from test_workflow.integ_test_suite import IntegTestSuite
from system.temporary_directory import TemporaryDirectory

DEPENDENCY_VERSION = '1.0'
common_dependencies = [
    'opensearch',
    'opensearch-build',
    'common-utils',
    'job-scheduler',
    'alerting'
]

def _get_dependency_repo(dep_name):
    pass

def parse_arguments():
    parser = argparse.ArgumentParser(description = "Test an OpenSearch Bundle")
    parser.add_argument('--manifest', type = argparse.FileType('r'), help="Manifest file.")
    parser.add_argument('--keep', dest = 'keep', action='store_true', help = "Do not delete the working temporary directory.")
    args = parser.parse_args()
    return args

#TODO: wip
def _get_opensearch_component(manifest):
    for component in manifest.components:
        if component.name == 'OpenSearch':
            return component

#TODO: wip
def pull_common_dependencies(manifest, work_dir):
    for dependency in common_dependencies:
        GitRepository(_get_dependency_repo(dependency), DEPENDENCY_VERSION, os.path.join(work_dir, dependency))
        #TODO: add the logic for copying dependencies in maven local
        pass

#TODO: wip
def pull_dependencies(component, work_dir):
    """
    TODO
    """
    repo = GitRepository(component.repository, component.commit_id, os.path.join(work_dir, component.name))
    pass


def is_component_test_supported(component):
    if component.name == 'anomaly-detection':
        return True
    else:
        return False


def run_plugin_integtests(manifest, component, work_dir):
    try:
        # Spin up a test cluster
        cluster = LocalTestCluster(manifest)
        cluster.create()
        print("plugin name: " + component.name)
        #TODO: (Create issue) Since plugins don't have integtest.sh in version branch, hardcoded it to main
        #repo = GitRepository(component.repository, component.commit_id, os.path.join(work_dir, component.name))
        repo = GitRepository(component.repository, 'main', os.path.join(work_dir, component.name))
        test_suite = IntegTestSuite(component.name, repo)
        test_suite.execute(cluster)
    finally:
        cluster.destroy()


def main():
    print("Starting here")
    args = parse_arguments()
    manifest = BundleManifest.from_file(args.manifest)
    print("Reading manifest file: %s" % args.manifest)
    with TemporaryDirectory(keep=args.keep) as work_dir:
        # Sample work_dir: /var/folders/d7/643j7dbj2yj0mq170_dpb621mwrhf4/T/tmpk17tk8li
        os.chdir(work_dir)
        # pull_common_dependencies(manifest, work_dir)
        # For each component, check out the git repo and run `integtest.sh`
        for component in manifest.components:
            if not is_component_test_supported(component):
                print('Skipping tests for %s, as it is currently not supported' % component.name)
                continue
    #         pull_dependencies(component)
            run_plugin_integtests(manifest, component, work_dir)

        # TODO: Store test results, send notification.


if __name__ == '__main__':
    sys.exit(main())
