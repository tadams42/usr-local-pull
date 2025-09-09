# https://github.com/astral-sh/uv
from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from ..app import BIN_PERM, DEFAULT_PREFIX, AppBinary, GitHubApp, ZshCompletion
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class Uv(GitHubApp):
    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(
            name="uv",
            prefix=prefix,
            gh_owner="astral-sh",
            gh_repo="uv",
            post_install_notice=None,
        )

    def download(self):
        asset_name = next(
            (
                a
                for a in self.client.latest_release.asset_names
                if a == "uv-x86_64-unknown-linux-gnu.tar.gz"
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

        exe = next((_ for _ in members if Path(_).name == "uv"), None)
        if not exe:
            raise ValueError(f"Can't find 'uv' in {asset_name}!")
        self.binary = AppBinary("uv", data=extractor.extract(exe))

        exe = next((_ for _ in members if Path(_).name == "uvx"), None)
        if not exe:
            raise ValueError(f"Can't find 'uvx' in {asset_name}!")
        self.other_bins = [AppBinary("uvx", data=extractor.extract(exe))]

        with tempfile.TemporaryDirectory() as tmp_dir:
            uv_path = Path(tmp_dir) / "uv_tmp"
            with uv_path.open("wb") as _:
                _.write(self.binary.data)
            uv_path.chmod(BIN_PERM)

            uvx_path = Path(tmp_dir) / "uvx_tmp"
            with uvx_path.open("wb") as _:
                _.write(self.other_bins[0].data)
            uvx_path.chmod(BIN_PERM)

            self.zsh_completions = [
                ZshCompletion(
                    app_name="uv",
                    data=subprocess.check_output(  # noqa: S603
                        [uv_path.as_posix(), "generate-shell-completion", "zsh"],
                        shell=False,
                    ),
                ),
                ZshCompletion(
                    app_name="uvx",
                    data=subprocess.check_output(  # noqa: S603
                        [uvx_path.as_posix(), "--generate-shell-completion", "zsh"],
                        shell=False,
                    ),
                ),
            ]
