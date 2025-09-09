from __future__ import annotations

import logging
from pathlib import Path

from ..app import DEFAULT_PREFIX, AppBinary, GitHubApp
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class Stylua(GitHubApp):

    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(
            name="stylua", prefix=prefix, gh_owner="JohnnyMorganz", gh_repo="stylua"
        )

    def download(self):
        asset_name = next(
            (
                a
                for a in self.client.latest_release.asset_names
                if a == "stylua-linux-x86_64.zip"
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

        exe = next((_ for _ in members if Path(_).name == "stylua"), None)
        if not exe:
            raise ValueError(f"Can't find 'stylua' in {asset_name}!")
        self.binary = AppBinary("stylua", data=extractor.extract(exe))
