# https://github.com/gitleaks/gitleaks
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from ..app import BIN_PERM, DEFAULT_PREFIX, AppBinary, GitHubApp, ZshCompletion
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class Gitleaks(GitHubApp):
    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(
            name="gitleaks",
            prefix=prefix,
            gh_owner="gitleaks",
            gh_repo="gitleaks",
            post_install_notice=None,
        )

    @property
    def installed_version(self):
        if self._installed_version:
            return self._installed_version
        self._installed_version = self.get_installed_version(self.name, -1)
        return self._installed_version

    def download(self):
        asset_name = next(
            (
                a
                for a in self.client.latest_release.asset_names
                if a.startswith("gitleaks_") and a.endswith("_linux_x64.tar.gz")
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

        exe = next((_ for _ in members if Path(_).name == "gitleaks"), None)
        if not exe:
            raise ValueError(f"Can't find 'gitleaks' in {asset_name}!")
        self.binary = AppBinary("gitleaks", data=extractor.extract(exe))

        with tempfile.TemporaryDirectory() as tmp_dir:
            exe_path = Path(tmp_dir) / f"{self.name}_tmp"
            with exe_path.open("wb") as _:
                _.write(self.binary.data)
            exe_path.chmod(BIN_PERM)

            self.zsh_completions = [
                ZshCompletion(
                    app_name="gitleaks",
                    data=subprocess.check_output(  # noqa: S603
                        [exe_path.as_posix(), "completion", "zsh"], shell=False
                    ),
                )
            ]
