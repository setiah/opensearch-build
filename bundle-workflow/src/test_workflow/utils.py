#!/usr/bin/env python

import os

from git.git_repository import GitRepository


def get_dependency_repo(dep_name):
    return "https://github.com/opensearch-project/" + dep_name + ".git"


def pull_plugin_repo(component, work_dir):
    GitRepository(component.repository, component.commit_id, os.path.join(work_dir, component.name))
