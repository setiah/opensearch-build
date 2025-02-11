#!/usr/bin/env python

import os
import argparse
from manifests.bundle_manifest import BundleManifest
from git.git_repository import GitRepository
from test_workflow.test_cluster import LocalTestCluster
from test_workflow.integ_test_suite import IntegTestSuite
from paths.script_finder import ScriptFinder
from system.temporary_directory import TemporaryDirectory

parser = argparse.ArgumentParser(description = "Test an OpenSearch Bundle")
parser.add_argument('manifest', type = argparse.FileType('r'), help = "Manifest file.")
parser.add_argument('--keep', dest = 'keep', action='store_true', help = "Do not delete the working temporary directory.")
args = parser.parse_args()

manifest = BundleManifest.from_file(args.manifest)
component_scripts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../scripts/bundle-build/components')
default_scripts_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../scripts/bundle-build/standard-test')
script_finder = ScriptFinder(component_scripts_path, default_scripts_path)

with TemporaryDirectory(keep = args.keep) as work_dir:
    os.chdir(work_dir)

    # Spin up a test cluster
    cluster = LocalTestCluster(manifest)
    cluster.create()

    # For each component, check out the git repo and run `integtest.sh`
    try:
        for component in manifest.components:
            print(component.name)
            repo = GitRepository(component.repository, component.commit_id, os.path.join(work_dir, component.name))
            test_suite = IntegTestSuite(component.name, repo)
            test_suite.execute(cluster)
    finally:
        cluster.destroy()

    # TODO: Store test results, send notification.
