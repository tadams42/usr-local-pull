from __future__ import annotations

import datetime
import json
import logging
import re
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from packaging.version import parse as parse_version

if TYPE_CHECKING:
    from typing import Any, Final

    from packaging.version import Version


logger = logging.getLogger(__name__)


@dataclass
class GhRelease:
    owner: str
    repo: str
    data: dict[str, Any] = field(default_factory=dict, repr=False)
    _version: Version = field(init=False)
    _downloaded_at: datetime.datetime = field(init=False)

    DOWNLOADED_AT_KEY: ClassVar[str] = "_downloaded_at"

    def __post_init__(self):
        if not self.data:
            raise ValueError(
                f"Missing GitHub release data for {self.owner}/{self.repo}!"
            )

        errs = []

        ver_str = self._cleanup_version_str(self.data.get("tag_name", None))
        version: Version | None = None
        try:
            version = parse_version(ver_str)
        except Exception as e:
            errs.append(str(e))

        if not version:
            ver_str = self._cleanup_version_str(self.data.get("name", None))
            try:
                version = parse_version(ver_str)
            except Exception as e:
                errs.append(str(e))

        downloaded_at: str | None = self.data.get(self.DOWNLOADED_AT_KEY)

        if not version or not downloaded_at:
            raise ValueError(
                f"Missing GitHub release version info for {self.owner}/{self.repo}!"
            )

        self._version = version
        self._downloaded_at = datetime.datetime.fromisoformat(downloaded_at)

    @classmethod
    def _cleanup_version_str(cls, v: str | None):
        if not v:
            return ""

        match = cls._CLEANER.match(v)
        if match:
            groups = match.groups()
            if groups:
                return groups[-1]

        return ""

    _CLEANER: ClassVar[re.Pattern] = re.compile(r"[^0-9]*(.*)")

    @property
    def downloaded_at(self) -> datetime.datetime:
        return self._downloaded_at

    @property
    def version(self) -> Version:
        return self._version

    @property
    def asset_names(self) -> list[str]:
        return [a["name"] for a in self.data.get("assets", [])]

    def asset_download_url(self, named: str) -> str | None:
        return next(
            (
                a["browser_download_url"]
                for a in self.data.get("assets", [])
                if a["name"] == named
            ),
            None,
        )

    def asset_id(self, named: str) -> int | None:
        return next(
            (a["id"] for a in self.data.get("assets", []) if a["name"] == named), None
        )

    @property
    def assets(self) -> list[dict[str, str | int | dict[str, str | int]]]:
        return self.data.get("assets", [])

    @property
    def tarball_url(self) -> str:
        return self.data["tarball_url"]

    @property
    def gh_id(self) -> int:
        return self.data["id"]


@dataclass
class GhDownloadedAsset:
    gh_id: int
    owner: str
    repo: str
    name: str
    data: bytes = field(default=b"", repr=False)
    tarball_name: str | None = None


@dataclass
class GhCache:
    _entries: dict[str, GhRelease | GhDownloadedAsset] = field(default_factory=dict)

    _RELEASE_CACHE_FOR_SECONDS: ClassVar[int] = 60 * 60

    @classmethod
    def _make_release_key(cls, owner: str, repo: str) -> str:
        return f"releases/{owner}/{repo}"

    @classmethod
    def _make_downloaded_asset_key(cls, gh_id: int, name: str) -> str:
        if name == "tarball":
            return f"downloaded_assets/tarball.{gh_id}"

        return f"downloaded_assets/asset.{gh_id}"

    @classmethod
    def _repo_cache_dir(cls, owner: str, repo: str) -> Path:
        retv = Path.home() / ".cache" / "usr-local-pull" / owner / repo
        if not retv.exists():
            retv.mkdir(parents=True, exist_ok=True)
        return retv

    def add_release(self, obj: GhRelease) -> None:
        data_path: Path = self._repo_cache_dir(obj.owner, obj.repo) / "release.json"

        with data_path.open("w") as f:
            json.dump(obj.data, f, indent=2)

        key = self._make_release_key(obj.owner, obj.repo)
        self._entries[key] = obj

    def get_release(self, owner: str, repo: str) -> GhRelease | None:
        key = self._make_release_key(owner, repo)
        now = datetime.datetime.now(datetime.UTC)

        retv: GhRelease | None = self._entries.get(key)  # type: ignore
        if retv:
            if (now - retv.downloaded_at).seconds > self._RELEASE_CACHE_FOR_SECONDS:
                return None
            logger.debug(
                "memory cache hit for %s/%s", owner, repo, extra={"app_name": repo}
            )
            return retv

        data_path: Path = self._repo_cache_dir(owner, repo) / "release.json"
        if data_path.exists():
            with data_path.open("r") as f:
                data = json.load(f)

            downloaded_at_s = data.get(GhRelease.DOWNLOADED_AT_KEY)
            if not downloaded_at_s:
                return None

            downloaded_at = datetime.datetime.fromisoformat(downloaded_at_s)
            if (now - downloaded_at).seconds > self._RELEASE_CACHE_FOR_SECONDS:
                return None

            logger.debug("disk cache hit for GitHub release", extra={"app_name": repo})

            entry = GhRelease(owner=owner, repo=repo, data=data)
            self._entries[key] = entry
            return entry

        return None

    def add_downloaded_asset(self, obj: GhDownloadedAsset) -> None:
        if obj.name == "tarball":
            data_path: Path = (
                self._repo_cache_dir(obj.owner, obj.repo) / f"tarball.{obj.gh_id}"
            )
        else:
            data_path: Path = (
                self._repo_cache_dir(obj.owner, obj.repo) / f"asset.{obj.gh_id}"
            )

        with data_path.open("wb") as f:
            f.write(obj.data)

        key = self._make_downloaded_asset_key(obj.gh_id, obj.name)
        self._entries[key] = obj

    def get_downloaded_asset(
        self, owner: str, repo: str, name: str, gh_id: int
    ) -> GhDownloadedAsset | None:
        key = self._make_downloaded_asset_key(gh_id, name)

        retv: GhDownloadedAsset | None = self._entries.get(key)  # type: ignore
        if retv:
            logger.debug("memory cache hit for %s", name, extra={"app_name": repo})
            return retv

        if name == "tarball":
            data_path: Path = self._repo_cache_dir(owner, repo) / f"tarball.{gh_id}"
        else:
            data_path: Path = self._repo_cache_dir(owner, repo) / f"asset.{gh_id}"
        if data_path.exists():
            logger.debug("disk cache hit for %s", name, extra={"app_name": repo})
            with data_path.open("rb") as f:
                data = f.read()
            entry = GhDownloadedAsset(
                gh_id=gh_id, owner=owner, repo=repo, name=name, data=data
            )
            self._entries[key] = entry
            return entry

        return None


_CACHE = GhCache()


class GithubApiClient:
    _GH_API_URL: Final[str] = "https://api.github.com/repos"

    def __init__(self, *, owner: str, repo: str) -> None:
        self.repo = repo
        self.owner = owner

    @property
    def latest_release(self) -> GhRelease:
        entry = _CACHE.get_release(self.owner, self.repo)
        if entry:
            return entry

        logger.info(
            "Fetching latest GitHub release info for %s/%s",
            self.owner,
            self.repo,
            extra={"app_name": self.repo},
        )
        request = urllib.request.Request(  # noqa: S310
            url=f"{self._GH_API_URL}/{self.owner}/{self.repo}/releases/latest",
            headers={"Accept": "application/vnd.github+json"},
        )
        data: dict[str, Any] | None = None

        try:
            with urllib.request.urlopen(request) as response:  # noqa: S310
                if response.status == 200:  # noqa: PLR2004
                    data = json.load(response)
        except Exception as e:
            raise ValueError(
                f"Can't fetch GitHub release info for {self.owner}/{self.repo}!"
            ) from e
        if not data:
            raise ValueError(
                f"Can't fetch GitHub release info for {self.owner}/{self.repo}!"
            )

        data[GhRelease.DOWNLOADED_AT_KEY] = datetime.datetime.now(
            datetime.UTC
        ).isoformat()
        entry = GhRelease(owner=self.owner, repo=self.repo, data=data)
        _CACHE.add_release(entry)

        return entry

    def downloaded_asset(self, named: str) -> GhDownloadedAsset:
        if named == "tarball":
            gh_id = self.latest_release.gh_id
        else:
            gh_id = self.latest_release.asset_id(named)
        if not gh_id:
            raise ValueError(f"No such asset name {named}!")

        entry: GhDownloadedAsset | None = _CACHE.get_downloaded_asset(
            self.owner, self.repo, named, gh_id
        )
        if entry:
            return entry

        if named == "tarball":
            url = self.latest_release.tarball_url
        else:
            url = self.latest_release.asset_download_url(named)
        if not url:
            raise ValueError(f"No such asset name {named}!")
        if not url.startswith(("http:", "https:")):
            raise ValueError("URL must be 'http:' or 'https:'!")

        logger.info("Downloading %s from GitHub.", named, extra={"app_name": self.repo})
        data: bytes | None = None
        try:
            with urllib.request.urlopen(url) as response:  # noqa: S310
                data = response.read()
        except Exception as e:
            raise ValueError(f"Couldn't download {named} from GitHub!") from e
        if not data:
            raise ValueError(f"Couldn't download {named} from GitHub!")

        logger.info("Downloaded %s from GitHub.", named, extra={"app_name": self.repo})
        entry = GhDownloadedAsset(
            owner=self.owner, repo=self.repo, name=named, data=data, gh_id=gh_id
        )
        _CACHE.add_downloaded_asset(entry)

        return entry
