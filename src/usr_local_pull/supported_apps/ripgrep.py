from __future__ import annotations

import logging
import subprocess
from typing import TYPE_CHECKING

from packaging.version import Version
from packaging.version import parse as parse_version

from ..app import DEFAULT_PREFIX, AppBinary, GitHubApp, ManPage, ZshCompletion
from ..archive_extractor import ArchiveExtractor

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class Ripgrep(GitHubApp):
    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(
            name="ripgrep", prefix=prefix, gh_owner="BurntSushi", gh_repo="ripgrep"
        )
        self._installed_version: Version | None = None

    @property
    def installed_version(self) -> Version | None:
        if self._installed_version:
            return self._installed_version

        try:
            bin_path = self.prefix / "bin" / "rg"
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
                if a == "ripgrep_14.1.1-1_amd64.deb"
            ),
            None,
        )
        if not asset_name:
            raise ValueError(
                f"Can't find suitable release asset in {self.client.latest_release.asset_names}!"
            )

        asset = self.client.downloaded_asset(asset_name)
        deb_extractor = ArchiveExtractor(asset.name, asset.data)
        xz_data = deb_extractor.extract("data.tar.xz")
        extractor = ArchiveExtractor("data.tar.xz", xz_data)
        members = extractor.members

        exe = next((_ for _ in members if _ == "usr/bin/rg"), None)
        if not exe:
            raise ValueError(f"Can't find 'ripgrep' in {asset_name}!")
        self.binary = AppBinary("rg", data=extractor.extract(exe))

        man = next((_ for _ in members if _ == "usr/share/man/man1/rg.1.gz"), None)
        if not man:
            raise ValueError(f"Can't find 'rg.1.gz' in {asset_name}!")
        self.man_pages.append(
            ManPage(section=1, file_name="rg.1.gz", data=extractor.extract(man))
        )

        zsh_complete = next(
            (_ for _ in members if _ == "usr/share/zsh/vendor-completions/_rg"), None
        )
        if not zsh_complete:
            raise ValueError(f"Can't find 'ripgrep.zsh' in {asset_name}!")
        self.zsh_completion = ZshCompletion("rg", data=extractor.extract(zsh_complete))
