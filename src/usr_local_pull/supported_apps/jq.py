from __future__ import annotations

import logging
from pathlib import Path

from ..app import DEFAULT_PREFIX, AppBinary, GitHubApp, ManPage
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class Jq(GitHubApp):
    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(name="jq", prefix=prefix, gh_owner="jqlang", gh_repo="jq")

    @property
    def installed_version(self):
        if self._installed_version:
            return self._installed_version
        self._installed_version = self.get_installed_version(self.name, -1)
        return self._installed_version

    def download(self):
        asset_name = next(
            (
                a
                for a in self.client.latest_release.asset_names
                if a.startswith("jq-") and a.endswith(".tar.gz")
            ),
            None,
        )
        if not asset_name:
            raise ValueError(
                f"Can't find suitable release asset in {self.client.latest_release.asset_names}!"
            )

        asset = self.client.downloaded_asset(asset_name)
        extractor = ArchiveExtractor(asset.name, asset.data)
        members = extractor.members

        man = next((_ for _ in members if Path(_).name == "jq.1"), None)
        if not man:
            raise ValueError(f"Can't find 'jq.1' in {asset_name}!")
        self.man_pages.append(
            ManPage(section=1, file_name="jq.1", data=extractor.extract(man))
        )

        asset_name = next(
            (
                a
                for a in self.client.latest_release.asset_names
                if a == "jq-linux-amd64"
            ),
            None,
        )
        if not asset_name:
            raise ValueError(
                f"Can't find binary release asset in {self.client.latest_release.asset_names}!"
            )
        exe = self.client.downloaded_asset(asset_name)
        self.binary = AppBinary("jq", data=exe.data)
