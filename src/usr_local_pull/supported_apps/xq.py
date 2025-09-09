from __future__ import annotations

import logging
from pathlib import Path

from ..app import DEFAULT_PREFIX, AppBinary, GitHubApp
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class Xq(GitHubApp):
    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(
            name="xq", prefix=prefix, gh_owner="sibprogrammer", gh_repo="xq"
        )

    @property
    def installed_version(self):
        if self._installed_version:
            return self._installed_version
        self._installed_version = self.get_installed_version(self.name, 2)
        return self._installed_version

    def download(self):
        asset_name = next(
            (
                a
                for a in self.client.latest_release.asset_names
                if a.startswith("xq_") and a.endswith("_linux_amd64.tar.gz")
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

        exe = next((_ for _ in members if Path(_).name == "xq"), None)
        if not exe:
            raise ValueError(f"Can't find 'xq' in {asset_name}!")
        self.binary = AppBinary("xq", data=extractor.extract(exe))
