# https://github.com/ast-grep/ast-grep
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from packaging.version import Version
from packaging.version import parse as parse_version

from ..app import DEFAULT_PREFIX, AppBinary, GitHubApp
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class AstGrep(GitHubApp):
    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(
            name="ast-grep", prefix=prefix, gh_owner="ast-grep", gh_repo="ast-grep"
        )
        self._installed_version: Version | None = None

    @property
    def installed_version(self) -> Version | None:
        if self._installed_version:
            return self._installed_version

        try:
            bin_path = self.prefix / "bin" / "ast-grep"
            if bin_path.exists():
                data = subprocess.check_output(  # noqa: S603
                    [bin_path.as_posix(), "--version"], shell=False, encoding="utf-8"
                )
                if data:
                    data = data.split()
                if data:
                    self._installed_version = parse_version(data[-1])
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
