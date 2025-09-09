from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

from ..app import BIN_PERM, DEFAULT_PREFIX, AppBinary, GitHubApp, ManPage, ZshCompletion
from ..archive_extractor import ArchiveExtractor

logger = logging.getLogger(__name__)


class YamlQ(GitHubApp):
    def __init__(self, prefix: str | Path = DEFAULT_PREFIX) -> None:
        super().__init__(name="yq", prefix=prefix, gh_owner="mikefarah", gh_repo="yq")

    def download(self):
        asset_name = next(
            (
                a
                for a in self.client.latest_release.asset_names
                if a == "yq_linux_amd64.tar.gz"
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

        exe = next((_ for _ in members if Path(_).name == "yq_linux_amd64"), None)
        if not exe:
            raise ValueError(f"Can't find 'yq_linux_amd64' in {asset_name}!")
        self.binary = AppBinary("yq", data=extractor.extract(exe))

        man = next((_ for _ in members if Path(_).name == "yq.1"), None)
        if not man:
            raise ValueError(f"Can't find 'yq.1' in {asset_name}!")
        self.man_pages.append(
            ManPage(section=1, file_name="yq.1", data=extractor.extract(man))
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            exe_path = Path(tmp_dir) / f"{self.name}_tmp"
            with exe_path.open("wb") as _:
                _.write(self.binary.data)
            exe_path.chmod(BIN_PERM)

            self.zsh_completions = [
                ZshCompletion(
                    app_name="yq",
                    data=subprocess.check_output(  # noqa: S603
                        [exe_path.as_posix(), "completion", "zsh"], shell=False
                    ),
                )
            ]
