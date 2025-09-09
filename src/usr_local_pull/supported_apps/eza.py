from __future__ import annotations

import logging
from pathlib import Path

from ..app import DEFAULT_PREFIX, AppBinary, GitHubApp, ManPage, ZshCompletion
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class Eza(GitHubApp):
    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(
            name="eza",
            prefix=prefix,
            gh_owner="eza-community",
            gh_repo="eza",
        )

    @property
    def installed_version(self):
        if self._installed_version:
            return self._installed_version
        self._installed_version = self.get_installed_version(self.name, -3)
        return self._installed_version

    def download(self):
        asset_name = next(
            (
                a
                for a in self.client.latest_release.asset_names
                if a == "eza_x86_64-unknown-linux-gnu.tar.gz"
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
        exe = next((_ for _ in members if Path(_).name == "eza"), None)
        if not exe:
            raise ValueError(f"Can't find 'eza' in {asset_name}!")
        self.binary = AppBinary("eza", data=extractor.extract(exe))

        asset_name = next(
            (
                a
                for a in self.client.latest_release.asset_names
                if a.startswith("completions-") and a.endswith(".tar.gz")
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
        zsh_complete = next((_ for _ in members if Path(_).name == "_eza"), None)
        if not zsh_complete:
            raise ValueError(f"Can't find '_eza' in {asset_name}!")
        self.zsh_completions = [
            ZshCompletion("eza", data=extractor.extract(zsh_complete))
        ]

        asset_name = next(
            (
                a
                for a in self.client.latest_release.asset_names
                if a.startswith("man-") and a.endswith(".tar.gz")
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
        for member in members:
            file_name = Path(member).name
            section = int(Path(member).suffixes[-1][1:])
            self.man_pages.append(
                ManPage(
                    section=section, file_name=file_name, data=extractor.extract(member)
                )
            )
