#!/usr/bin/env python

import argparse
import os
import subprocess
import sys

from git.git_repository import GitRepository
from test_workflow.local_test_cluster import LocalTestCluster
from test_workflow.integ_test_workflow.integ_test_suite import IntegTestSuite
from system.temporary_directory import TemporaryDirectory
from test_workflow import utils
from manifests.build_manifest import BuildManifest
from manifests.bundle_manifest import BundleManifest

# DEPENDENCY_VERSION = '1.0'

# TODO: 1. log test related logging into a log file. Output only workflow logs on shell.
# TODO: 2. Move common functions to utils.py


def parse_arguments():
    parser = argparse.ArgumentParser(description="Test an OpenSearch Bundle")
    parser.add_argument('--bundle-manifest', type=argparse.FileType('r'), help="Bundle Manifest file.")
    parser.add_argument('--build-manifest', type=argparse.FileType('r'), help="Build Manifest file.")
    parser.add_argument('--keep', dest='keep', action='store_true',
                        help="Do not delete the working temporary directory.")
    args = parser.parse_args()
    return args


# def _get_common_dependencies():
#     return {
#         'opensearch': DEPENDENCY_VERSION,
#         'opensearch-build': 'main',
#         'common-utils': DEPENDENCY_VERSION,
#         'job-scheduler': DEPENDENCY_VERSION,
#         'alerting': DEPENDENCY_VERSION
#     }


def _get_common_dependencies():
    return [
        'opensearch',
        'opensearch-build',
        'common-utils',
        'job-scheduler',
        'alerting'
    ]


# TODO: replace with DependencyProvider - https://github.com/opensearch-project/opensearch-build/issues/283
def pull_common_dependencies(work_dir, build_manifest):
    common_dependencies = _get_common_dependencies()
    for component in build_manifest.components:
        if component.name in common_dependencies:
            GitRepository(component.repository, component.commit_id, os.path.join(work_dir, component.name))
    # for dependency, branch in common_dependencies.items():
    #     GitRepository(utils.get_dependency_repo(dependency), branch, os.path.join(work_dir, dependency))


# TODO: replace with DependencyProvider - https://github.com/opensearch-project/opensearch-build/issues/283
def sync_maven_dependencies(component, work_dir, manifest_build_ver):
    os.chdir(work_dir + "/opensearch")
    subprocess.run(work_dir + '/opensearch-build/tools/standard-test/integtest_dependencies_opensearch.sh opensearch ' + manifest_build_ver, shell=True)
    os.chdir(work_dir + '/common-utils')
    subprocess.run(work_dir + '/opensearch-build/tools/standard-test/integtest_dependencies_opensearch.sh common-utils ' + manifest_build_ver, shell=True)
    os.chdir(work_dir)
    subprocess.run('mv -v job-scheduler ' + component.name, shell=True)
    os.chdir(work_dir + '/' + component.name + '/job-scheduler')
    subprocess.run(work_dir + '/opensearch-build/tools/standard-test/integtest_dependencies_opensearch.sh job-scheduler ' + manifest_build_ver, shell=True)
    os.chdir(work_dir)
    subprocess.run('mv alerting notifications', shell=True)
    os.chdir(work_dir + '/'+ '/notifications')
    subprocess.run(work_dir + '/opensearch-build/tools/standard-test/integtest_dependencies_opensearch.sh alerting ' + manifest_build_ver, shell=True)


def is_component_test_supported(component):
    if component.name == 'index-management':
        return True
    else:
        return False


def run_component_integ_tests(manifest, component, work_dir):
    try:
        # Spin up a test cluster
        cluster = LocalTestCluster(manifest, work_dir)
        cluster.create()
        print("component name: " + component.name)
        # TODO: (Create issue) Since plugins don't have integtest.sh in version branch, hardcoded it to main
        # repo = GitRepository(component.repository, component.commit_id, os.path.join(work_dir, component.name))
        repo = GitRepository(component.repository, 'main', os.path.join(work_dir, component.name))
        test_suite = IntegTestSuite(component.name, repo)
        test_suite.execute(cluster)
    finally:
        cluster.destroy()


def main():
    args = parse_arguments()
    print("Reading manifest file: %s" % args.manifest)
    bundle_manifest = BundleManifest.from_file(args.bundle_manifest)
    build_manifest = BuildManifest.from_file(args.build_manifest)
    with TemporaryDirectory(keep=args.keep) as work_dir:
        # Sample work_dir: /var/folders/d7/643j7dbj2yj0mq170_dpb621mwrhf4/T/tmpk17tk8li
        print("Switching to temporary work_dir: " + work_dir)
        os.chdir(work_dir)
        pull_common_dependencies(work_dir, build_manifest)
        for component in bundle_manifest.components:
            if not is_component_test_supported(component):
                print('Skipping tests for %s, as it is currently not supported' % component.name)
                continue
            utils.pull_plugin_repo(component, work_dir)
            sync_maven_dependencies(component, work_dir, bundle_manifest.build.version)
            #run_component_integ_tests(bundle_manifest, component, work_dir)
            # TODO: Store test results

        # TODO: send notification.


if __name__ == '__main__':
    sys.exit(main())
