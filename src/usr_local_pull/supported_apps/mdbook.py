from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from ..app import BIN_PERM, DEFAULT_PREFIX, AppBinary, GitHubApp, ZshCompletion
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class Mdbook(GitHubApp):

    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(
            name="mdbook", prefix=prefix, gh_owner="rust-lang", gh_repo="mdBook"
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
                if a.startswith("mdbook-")
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

        exe = next((_ for _ in members if Path(_).name == "mdbook"), None)
        if not exe:
            raise ValueError(f"Can't find 'mdbook' in {asset_name}!")
        self.binary = AppBinary("mdbook", data=extractor.extract(exe))

        with tempfile.TemporaryDirectory() as tmp_dir:
            exe_path = Path(tmp_dir) / f"{self.name}_tmp"
            with exe_path.open("wb") as _:
                _.write(self.binary.data)
            exe_path.chmod(BIN_PERM)

            self.zsh_completions = [
                ZshCompletion(
                    app_name="mdbook",
                    data=subprocess.check_output(  # noqa: S603
                        [exe_path.as_posix(), "completions", "zsh"], shell=False
                    ),
                )
            ]
