from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from packaging.version import Version
from packaging.version import parse as parse_version

from ..app import DEFAULT_PREFIX, AppBinary, GitHubApp
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class Neovide(GitHubApp):
    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(
            name="neovide", prefix=prefix, gh_owner="neovide", gh_repo="neovide"
        )
        self._installed_version: Version | None = None

    @property
    def installed_version(self) -> Version | None:
        if self._installed_version:
            return self._installed_version

        try:
            bin_path = self.prefix / "bin" / "neovide"
            if bin_path.exists():
                data = subprocess.check_output(  # noqa: S603
                    [bin_path.as_posix(), "--version"],
                    shell=False,
                    encoding="utf-8",
                    stderr=subprocess.STDOUT,
                )
                if data:
                    data = data.split()
                if data and len(data) >= 1:
                    self._installed_version = parse_version(data[-1])
            if self._installed_version:
                logger.debug(
                    "Found installed version %s",
                    self._installed_version,
                    extra={"app_name": self.name},
                )

        except subprocess.CalledProcessError:
            logger.warning(
                "neovide failed to report it's version. This is known problem with "
                "version 0.13.3 where `neovide --version` command occasionally "
                "coredumps. Assuming version `0.13.3` and hoping it will be fixed in "
                "future versions..."
            )
            self._installed_version = parse_version("0.13.3")

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
                if a == "neovide-linux-x86_64.tar.gz"
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

        exe = next((_ for _ in members if Path(_).name == "neovide"), None)
        if not exe:
            raise ValueError(f"Can't find 'neovide' in {asset_name}!")
        self.binary = AppBinary("neovide", data=extractor.extract(exe))
