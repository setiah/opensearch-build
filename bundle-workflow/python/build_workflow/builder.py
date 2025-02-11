# Copyright OpenSearch Contributors.
# SPDX-License-Identifier: Apache-2.0

import os

'''
This class is responsible for executing the build for a component and passing the results to a build recorder.
It will notify the build recorder of build information such as repository and git ref, and any artifacts generated by the build.
Artifacts found in "<build root>/artifacts/<maven|plugins|libs|bundle>" will be recognized and recorded.
'''
class Builder:
    def __init__(self, component_name, git_repo, script_finder, build_recorder):
        '''
        Construct a new Builder instance.
        :param component_name: The name of the component to build.
        :param git_repo: A GitRepository instance containing the checked-out code.
        :param script_finder: The ScriptFinder to use for finding build.sh scripts.
        :param build_recorder: The build recorder that will capture build information and artifacts.
        '''

        self.component_name = component_name
        self.git_repo = git_repo
        self.script_finder = script_finder
        self.build_recorder = build_recorder
        self.output_path = 'artifacts'

    def build(self, version, arch, snapshot):
        build_script = self.script_finder.find_build_script(self.component_name, self.git_repo.dir)
        build_command = f'{build_script} -v {version} -a {arch} -s {str(snapshot).lower()} -o {self.output_path}'
        self.git_repo.execute(build_command)
        self.build_recorder.record_component(self.component_name, self.git_repo)

    def export_artifacts(self):
        artifacts_dir = os.path.realpath(os.path.join(self.git_repo.dir, self.output_path))
        for artifact_type in ["maven", "bundle", "plugins", "libs"]:
            for dir, dirs, files in os.walk(os.path.join(artifacts_dir, artifact_type)):
                for file_name in files:
                    absolute_path = os.path.join(dir, file_name)
                    relative_path = os.path.relpath(absolute_path, artifacts_dir)
                    self.build_recorder.record_artifact(self.component_name, artifact_type, relative_path, absolute_path)
