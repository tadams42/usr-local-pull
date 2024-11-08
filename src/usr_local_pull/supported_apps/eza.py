from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from packaging.version import Version
from packaging.version import parse as parse_version

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
        self._installed_version: Version | None = None

    @property
    def installed_version(self) -> Version | None:
        if self._installed_version:
            return self._installed_version

        try:
            bin_path = self.prefix / "bin" / "eza"
            if bin_path.exists():
                data = subprocess.check_output(  # noqa: S603
                    [bin_path.as_posix(), "--version"], shell=False, encoding="utf-8"
                )
                if data:
                    data = data.split("\n")
                if data and len(data) >= 2:  # noqa: PLR2004
                    data = data[1]
                if data and len(data) >= 1:
                    data = data.split()
                    self._installed_version = parse_version(data[0])
            if self._installed_version:
                logger.debug(
                    "Found installed version %s",
                    self._installed_version,
                    extra={"app_name": self.name},
                )
        except Exception as e:
            raise RuntimeError(
                f"Failed to fetch local app version for {self.name}!"
            ) from e

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
        self.zsh_completion = ZshCompletion("eza", data=extractor.extract(zsh_complete))

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
