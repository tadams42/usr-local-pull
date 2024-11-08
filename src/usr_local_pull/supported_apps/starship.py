from __future__ import annotations

import logging
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Final

from packaging.version import Version
from packaging.version import parse as parse_version

from ..app import BIN_PERM, DEFAULT_PREFIX, AppBinary, GitHubApp, ZshCompletion
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class Starship(GitHubApp):
    _POST_INSTALL_NOTICE: Final[str] = textwrap.dedent(
        """
        add to .zshrc: `eval "$(starship init zsh)`
        """
    )

    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(
            name="starship",
            prefix=prefix,
            gh_owner="starship",
            gh_repo="starship",
            post_install_notice=self._POST_INSTALL_NOTICE,
        )
        self._installed_version: Version | None = None

    @property
    def installed_version(self) -> Version | None:
        if self._installed_version:
            return self._installed_version

        try:
            bin_path = self.prefix / "bin" / "starship"
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
                if a == "starship-x86_64-unknown-linux-gnu.tar.gz"
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

        exe = next((_ for _ in members if Path(_).name == "starship"), None)
        if not exe:
            raise ValueError(f"Can't find 'starship' in {asset_name}!")
        self.binary = AppBinary("starship", data=extractor.extract(exe))

        with tempfile.TemporaryDirectory() as tmp_dir:
            exe_path = Path(tmp_dir) / f"{self.name}_tmp"
            with exe_path.open("wb") as _:
                _.write(self.binary.data)
            exe_path.chmod(BIN_PERM)

            self.zsh_completion = ZshCompletion(
                app_name="starship",
                data=subprocess.check_output(  # noqa: S603
                    [exe_path.as_posix(), "completions", "zsh"], shell=False
                ),
            )
