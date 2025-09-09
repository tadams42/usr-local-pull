# https://github.com/rust-lang/rust-analyzer
#
# also, as a rustup component:
#
#    $ rustup component add rust-analyzer
from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from packaging.version import Version
from packaging.version import parse as parse_version

from ..app import DEFAULT_PREFIX, AppBinary, GitHubApp
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class RustAnalyzer(GitHubApp):
    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(
            name="rust-analyzer",
            prefix=prefix,
            gh_owner="rust-lang",
            gh_repo="rust-analyzer",
        )
        self._installed_version: Version | None = None

    @property
    def installed_version(self) -> Version | None:
        if self._installed_version:
            return self._installed_version

        try:
            bin_path = self.prefix / "bin" / "rust-analyzer"
            if bin_path.exists():
                data = subprocess.check_output(  # noqa: S603
                    [bin_path.as_posix(), "--version"], shell=False, encoding="utf-8"
                )
                if data:
                    data = data.replace("-", " ").split()[-2]
                if data:
                    self._installed_version = parse_version(data)
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
                if a == "rust-analyzer-x86_64-unknown-linux-gnu.gz"
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

        exe = next(
            (
                _
                for _ in members
                if Path(_).name == "rust-analyzer-x86_64-unknown-linux-gnu"
            ),
            None,
        )
        if not exe:
            raise ValueError(f"Can't find 'rust-analyzer' in {asset_name}!")
        self.binary = AppBinary("rust-analyzer", data=extractor.extract(exe))
