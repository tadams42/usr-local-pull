from __future__ import annotations

import logging
from pathlib import Path

from ..app import DEFAULT_PREFIX, AppBinary, GitHubApp, ManPage, ZshCompletion
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class Bat(GitHubApp):
    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(name="bat", prefix=prefix, gh_owner="sharkdp", gh_repo="bat")

    @property
    def installed_version(self):
        if self._installed_version:
            return self._installed_version
        self._installed_version = self.get_installed_version(self.name, 1)
        return self._installed_version

    def download(self):
        asset_name = next(
            (
                a
                for a in self.client.latest_release.asset_names
                if a.startswith("bat-")
                and a.endswith("-x86_64-unknown-linux-gnu.tar.gz")
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

        errs = []

        exe = next((_ for _ in members if Path(_).name == "bat"), None)
        if not exe:
            errs.append(f"Can't find 'bat' in {asset_name}!")

        man = next((_ for _ in members if Path(_).name == "bat.1"), None)
        if not man:
            errs.append(f"Can't find 'bat.1' in {asset_name}!")

        zsh_complete = next((_ for _ in members if Path(_).name == "bat.zsh"), None)
        if not zsh_complete:
            errs.append(f"Can't find 'bat.zsh' in {asset_name}!")

        if errs:
            raise ValueError(f"Asset extraction failed: {errs}!")

        self.binary = AppBinary("bat", data=extractor.extract(exe))
        self.zsh_completions = [
            ZshCompletion("bat", data=extractor.extract(zsh_complete))
        ]
        self.man_pages.append(
            ManPage(section=1, file_name="bat.1", data=extractor.extract(man))
        )
