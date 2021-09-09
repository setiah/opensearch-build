# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.
#
# Modifications Copyright OpenSearch Contributors. See
# GitHub history for details.

class BundleInfoProvider:

    @staticmethod
    def get_tarball_relative_location(build_id, opensearch_version, architecture):
        return f"bundles/{opensearch_version}/{build_id}/{architecture}/opensearch-{opensearch_version}-linux-{architecture}.tar.gz"

    @staticmethod
    def get_tarball_name(opensearch_version, architecture):
        return f"opensearch-{opensearch_version}-linux-{architecture}.tar.gz"

    @staticmethod
    def get_bundle_manifest_relative_location(build_id, opensearch_version, architecture):
        return f"bundles/{opensearch_version}/{build_id}/{architecture}/manifest.yml"

    @staticmethod
    def get_build_manifest_relative_location(build_id, opensearch_version, architecture):
        return f"builds/{opensearch_version}/{build_id}/{architecture}/manifest.yml"
