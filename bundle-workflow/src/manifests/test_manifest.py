# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

import yaml


class TestManifest:
    """
    A BundleManifest is an immutable view of the outputs from a assemble step
    The manifest contains information about the bundle that was built (in the `assemble` section),
    and the components that made up the bundle in the `components` section.

    The format for schema version 1.0 is:
        schema-version: 1.0
        build:
          name: string
          version: string
          architecture: x64 or arm64
          location: /relative/path/to/tarball
        components:
          - name: string
            repository: URL of git repository
            ref: git ref that was built (sha, branch, or tag)
            commit_id: The actual git commit ID that was built (i.e. the resolved "ref")
            location: /relative/path/to/artifact
    """

    @staticmethod
    def from_file(file):
        return TestManifest(yaml.safe_load(file))

    def __init__(self, data):
        self.version = str(data["schema-version"])
        if self.version != "1.0":
            raise ValueError(f"Unsupported schema version: {self.version}")
        self.components = list(
            map(lambda entry: self.Component(entry), data["components"])
        )

    def to_dict(self):
        return {
            "schema-version": "1.0",
            "components": list(
                map(lambda component: component.to_dict(), self.components)
            ),
        }

    class Component:
        def __init__(self, data):
            self.name = data["name"]
            self.integ_test = data["integ-test"]
            self.bwc_test = data["bwc-test"]

        def to_dict(self):
            return {
                "name": self.name,
                "integTest": self.integ_test,
                "bwcTest": self.bwc_test
            }
