from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from ..app import BIN_PERM, DEFAULT_PREFIX, AppBinary, GitHubApp, ManPage, ZshCompletion
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class Dasel(GitHubApp):
    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(
            name="dasel", prefix=prefix, gh_owner="TomWright", gh_repo="dasel"
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
                if a == "dasel_linux_amd64.gz"
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

        exe = next((_ for _ in members if Path(_).name == "dasel_linux_amd64"), None)
        if not exe:
            raise ValueError(f"Can't find 'dasel_linux_amd64' in {asset_name}!")
        self.binary = AppBinary("dasel", data=extractor.extract(exe))

        with tempfile.TemporaryDirectory() as tmp_dir:
            exe_path = Path(tmp_dir) / f"{self.name}_tmp"
            with exe_path.open("wb") as _:
                _.write(self.binary.data)
            exe_path.chmod(BIN_PERM)

            self.zsh_completions = [
                ZshCompletion(
                    app_name="dasel",
                    data=subprocess.check_output(  # noqa: S603
                        [exe_path.as_posix(), "completion", "zsh"], shell=False
                    ),
                )
            ]

            mans_dir = Path(tmp_dir) / "mans"
            mans_dir.mkdir(exist_ok=True)

            _ = (
                subprocess.check_output(  # noqa: S603
                    [
                        exe_path.as_posix(),
                        "man",
                        "--output-directory",
                        mans_dir.as_posix(),
                    ],
                    shell=False,
                ),
            )

            for man_file_path in mans_dir.glob("*.1"):
                with man_file_path.open("rb") as f:
                    data = f.read()
                self.man_pages.append(
                    ManPage(section=1, file_name=man_file_path.name, data=data)
                )
