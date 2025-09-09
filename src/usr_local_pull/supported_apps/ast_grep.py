# https://github.com/ast-grep/ast-grep
from __future__ import annotations

import logging
from pathlib import Path

from ..app import DEFAULT_PREFIX, AppBinary, GitHubApp
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class AstGrep(GitHubApp):
    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(
            name="ast-grep", prefix=prefix, gh_owner="ast-grep", gh_repo="ast-grep"
        )

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
                if a == "app-x86_64-unknown-linux-gnu.zip"
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

        exe = next((_ for _ in members if Path(_).name == "ast-grep"), None)
        if not exe:
            raise ValueError(f"Can't find 'ast-grep' in {asset_name}!")
        self.binary = AppBinary("ast-grep", data=extractor.extract(exe))

        exe = next((_ for _ in members if Path(_).name == "sg"), None)
        if not exe:
            raise ValueError(f"Can't find 'sg' in {asset_name}!")
        self.other_bins = [AppBinary("sg", data=extractor.extract(exe))]
