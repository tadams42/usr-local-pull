from __future__ import annotations

import contextlib
import logging
import stat
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from packaging.version import Version
from packaging.version import parse as parse_version

from .gh_client import GithubApiClient

if TYPE_CHECKING:
    from datetime import date

    from packaging.version import Version


logger = logging.getLogger(__name__)

# Default install prefix for everything.
#
# Following `make` and many other packaging tools traditions, it should be `/usr/local`.
#
# PREFIX="/usr"       - Stuff built by and installed from Linux distribution packages
# PREFIX="/usr/local" - Stuff built by and installed by local admins (ie. `make install`
#                       and similar commands). When system package is updated, it
#                       doesn't overwrite locally built alternative
# PREFIX="/opt"       - Stuff installed from external sources and maybe not even
#                       packaged by hosting distribution standards (ie. doesn't keep
#                       config in /etc, variable data in /var, etc...)
DEFAULT_PREFIX = Path("/usr/local")

BIN_PERM: int = (
    stat.S_IRUSR  # Owner has read permission.
    | stat.S_IWUSR  # Owner has write permission.
    | stat.S_IXUSR  # Owner has execute permission.
    | stat.S_IRGRP  # Group has read permission.
    | stat.S_IXGRP  # Group has execute permission.
    | stat.S_IXOTH  # Others have execute permission.
    | stat.S_IROTH  # Others have read permission.
)

DOC_PERM: int = (
    stat.S_IRUSR  # Owner has read permission.
    | stat.S_IWUSR  # Owner has write permission.
    | stat.S_IRGRP  # Group has read permission.
    | stat.S_IROTH  # Others have read permission.
)


@dataclass
class ManPage:
    section: int
    file_name: str
    data: bytes = field(default=b"", repr=False)

    def install_path(self, prefix: Path = DEFAULT_PREFIX) -> Path:
        return prefix / "share" / "man" / f"man{self.section}" / self.file_name


@dataclass
class ZshCompletion:
    app_name: str
    data: bytes = field(default=b"", repr=False)
    _file_name: str = field(init=False)

    def __post_init__(self):
        self._file_name = f"_{self.app_name}"

    @property
    def file_name(self) -> str:
        return self._file_name

    def install_path(self, prefix: Path = DEFAULT_PREFIX) -> Path:
        # ZSH manual says vendor supplied functions should be in:
        #
        #     $PREFIX/share/zsh/site-functions
        #
        # Various Linux distributions additionally use:
        #
        #     $PREFIX/share/zsh/vendor-functions
        #     $PREFIX/share/zsh/vendor-completions
        #
        # But then don't necessarily include these in `$fpath`:`
        #
        #     /usr/local/share/zsh/vendor-functions
        #     /usr/local/share/zsh/vendor-completions
        #
        # This is, of course, because nothing from official Linux distribution repos
        # gets installed in `$PREFIX=/ur/local`.
        #
        # What IS included in `$fpath` (probably because ZSH does it regardless of Linux
        # distro):
        #
        #     `/usr/local/share/zsh/site-functions`
        #
        # Since this script is intended to be used for `/usr/local` installs anyway, we
        # can safely use that and don't care about distro speciffic things
        return prefix / "share" / "zsh" / "site-functions" / self.file_name


@dataclass
class AppBinary:
    app_name: str
    data: bytes = field(default=b"", repr=False)

    def install_path(self, prefix: Path = DEFAULT_PREFIX) -> Path:
        return prefix / "bin" / self.app_name


class App(ABC):
    def __init__(
        self,
        *,
        name: str,
        prefix: str | Path = DEFAULT_PREFIX,
        post_install_notice: str | None = None,
    ) -> None:
        self.name = name
        self.prefix: Path = Path(prefix) or DEFAULT_PREFIX
        self.post_install_notice: str | None = post_install_notice

        self.binary: AppBinary | None = None
        self.other_bins: list[AppBinary] | None = None
        self.zsh_completions: list[ZshCompletion] | None = None
        self.man_pages: list[ManPage] = []

    @property
    @abstractmethod
    def installed_version(self) -> Version | None:
        pass

    @property
    @abstractmethod
    def latest_available_version(self) -> Version | date:
        pass

    @property
    def needs_install(self) -> bool:
        return self.installed_version is None or (
            self.installed_version is not None
            and self.latest_available_version is not None
            and self.installed_version != self.latest_available_version
        )

    @abstractmethod
    def download(self):
        """
        Unconditionally download all app's assets and populate:

        - self.binary
        - self.zsh_completions
        - self.man_pages
        - self.other_bins
        """

    def install(self) -> list[Path]:
        installed_files: list[Path] = []

        if not self.needs_install:
            logger.info(
                "Already at latest version: '%s'...",
                self.installed_version,
                extra={"app_name": self.name},
            )

        else:
            self.download()

            if not self.binary:
                raise ValueError(f"Downloaded app {self.name} has no executable")

            bin_path = self.binary.install_path(prefix=self.prefix)
            if not bin_path.parent.exists():
                bin_path.parent.mkdir(parents=True)
            with bin_path.open("wb") as f:
                f.write(self.binary.data)
            bin_path.chmod(BIN_PERM)
            installed_files.append(bin_path)

            for bin in self.other_bins or []:
                bin_path = bin.install_path(prefix=self.prefix)
                if not bin_path.parent.exists():
                    bin_path.parent.mkdir(parents=True)
                with bin_path.open("wb") as f:
                    f.write(self.binary.data)
                bin_path.chmod(BIN_PERM)
                installed_files.append(bin_path)

            installed_files.extend(self._install_zsh_completions())
            installed_files.extend(self._install_man_pages())

            logger.info(
                "Installed %s.",
                self.latest_available_version,
                extra={"app_name": self.name},
            )

        return installed_files

    def _install_zsh_completions(self):
        retv = []

        if self.zsh_completions:
            for _ in self.zsh_completions:
                zsh_path = _.install_path(prefix=self.prefix)
                if not zsh_path.parent.exists():
                    zsh_path.parent.mkdir(parents=True)
                with zsh_path.open("wb") as f:
                    f.write(_.data)
                zsh_path.chmod(DOC_PERM)
                retv.append(zsh_path)

        return retv

    def _install_man_pages(self):
        retv = []

        for man in self.man_pages:
            man_path = man.install_path(prefix=self.prefix)
            if not man_path.parent.exists():
                man_path.parent.mkdir(parents=True)
            with man_path.open("wb") as f:
                f.write(man.data)
            man_path.chmod(DOC_PERM)
            retv.append(man_path)

        return retv


class GitHubApp(App):
    def __init__(
        self,
        *,
        name: str,
        prefix: str | Path = DEFAULT_PREFIX,
        post_install_notice: str | None = None,
        gh_owner: str,
        gh_repo: str,
    ) -> None:
        super().__init__(
            name=name, prefix=prefix, post_install_notice=post_install_notice
        )
        self.client = GithubApiClient(owner=gh_owner, repo=gh_repo)
        self._installed_version: Version | None = None

    @property
    def latest_available_version(self):
        return self.client.latest_release.version

    @property
    def installed_version(self) -> Version | None:
        if self._installed_version:
            return self._installed_version
        self._installed_version = self.get_installed_version(self.name, -1)
        return self._installed_version

    def get_installed_version(
        self, exe_name: str, version_str_idx: int = -1
    ) -> Version | None:
        retv = None

        try:
            bin_path = self.prefix / "bin" / exe_name
            if bin_path.exists():
                data = subprocess.check_output(  # noqa: S603
                    [bin_path.as_posix(), "--version"], shell=False, encoding="utf-8"
                )

                with contextlib.suppress(Exception):
                    _ = data.split()
                    retv = parse_version(_[version_str_idx])

                if not retv:
                    _ = data.replace("-", " ").split()
                    retv = parse_version(_[version_str_idx])

            if retv:
                logger.debug(
                    "Found installed version %s", retv, extra={"app_name": self.name}
                )
        except Exception as e:
            raise RuntimeError(
                f"Failed to fetch local app version for {self.name}!"
            ) from e

        return retv
