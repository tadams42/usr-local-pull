from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from packaging.version import Version
from packaging.version import parse as parse_version

from ..app import DEFAULT_PREFIX, AppBinary, GitHubApp, ManPage, ZshCompletion
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class FdFind(GitHubApp):
    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(name="fd", prefix=prefix, gh_owner="sharkdp", gh_repo="fd")
        self._installed_version: Version | None = None

    @property
    def installed_version(self) -> Version | None:
        if self._installed_version:
            return self._installed_version

        try:
            bin_path = self.prefix / "bin" / "fd"
            if bin_path.exists():
                data = subprocess.check_output(  # noqa: S603
                    [bin_path.as_posix(), "--version"], shell=False, encoding="utf-8"
                )
                if data:
                    data = data.split()
                if data and len(data) >= 2:  # noqa: PLR2004
                    self._installed_version = parse_version(data[1])
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
                if a.startswith("fd-")
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

        exe = next((_ for _ in members if Path(_).name == "fd"), None)
        if not exe:
            errs.append(f"Can't find 'fd' in {asset_name}!")

        man = next((_ for _ in members if Path(_).name == "fd.1"), None)
        if not man:
            errs.append(f"Can't find 'fd.1' in {asset_name}!")

        zsh_complete = next((_ for _ in members if Path(_).name == "_fd"), None)
        if not zsh_complete:
            errs.append(f"Can't find '_fd' in {asset_name}!")

        if errs:
            raise ValueError(f"Asset extraction failed: {errs}!")

        self.binary = AppBinary("fd", data=extractor.extract(exe))
        self.zsh_completion = ZshCompletion("fd", data=extractor.extract(zsh_complete))
        self.man_pages.append(
            ManPage(section=1, file_name="fd.1", data=extractor.extract(man))
        )
