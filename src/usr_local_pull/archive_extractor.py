import gzip
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path

import ar


class ArchiveExtractor:
    def __init__(self, archive: str | Path, data: bytes) -> None:
        self.archive = Path(archive)
        self.file = BytesIO(data)
        self._members: list[str] | None = None

    @property
    def members(self) -> list[str]:  # noqa: C901
        if self._members is not None:
            return self._members

        if self._is_tar:
            self._members = []
            self.file.seek(0)
            with tarfile.open(
                name=self.archive.name, fileobj=self.file, mode=self._tar_read_mode  # type: ignore
            ) as tar:  # type: ignore
                for member in tar.getmembers():
                    if member.isfile():
                        self._members.append(member.path)

        elif self._is_zip:
            self._members = []
            self.file.seek(0)
            with zipfile.ZipFile(file=self.file) as zipf:
                for member in zipf.infolist():
                    if not member.is_dir():
                        self._members.append(member.filename)

        elif self._is_ar:
            self._members = []
            self.file.seek(0)
            archive = ar.Archive(self.file)
            for entry in archive:
                self._members.append(entry.name)

        elif self._is_gzip:
            self._members = [Path(self.archive).name[:-3]]

        else:
            raise ValueError(f"Unsupported asset type {self.archive}!")

        return self._members

    def extract(self, member: str) -> bytes:  # noqa: C901
        retv: bytes | None = None

        if self._is_tar:
            self._members = []
            self.file.seek(0)
            with tarfile.open(
                name=self.archive.name, fileobj=self.file, mode=self._tar_read_mode  # type: ignore
            ) as tar:  # type: ignore
                for member_info in tar.getmembers():
                    if member_info.isfile() and member_info.path == member:
                        retv = tar.extractfile(member_info).read()

        elif self._is_zip:
            self.file.seek(0)
            with zipfile.ZipFile(file=self.file) as zip_f:
                for member_info in zip_f.infolist():
                    if not member_info.is_dir() and member_info.filename == member:
                        with zip_f.open(member_info) as member_f:
                            retv = member_f.read()
        elif self._is_ar:
            self.file.seek(0)
            archive = ar.Archive(self.file)
            for entry in archive:
                retv = archive.open(entry, "rb").read()

        elif self._is_gzip:
            self.file.seek(0)
            with gzip.GzipFile(fileobj=self.file, mode="rb") as gzip_f:
                retv = gzip_f.read()

        if retv is None:
            raise ValueError("No such file!")

        return retv

    @property
    def _tar_read_mode(self) -> str | None:
        ext = self.archive.suffixes[-1].lower()
        return {".gz": "r:gz", ".bz2": "r:bz2", ".xz": "r:xz", ".tar": "r:"}.get(ext)

    @property
    def _is_tar(self) -> bool:
        # ext = "".join(self.archive.suffixes).lower()
        return self.archive.name.lower().endswith(
            (
                ".tar.gz",
                ".tar.bz2",
                ".tar.xz",
                ".tar",
            )
        )

    @property
    def _is_zip(self) -> bool:
        ext = "".join(self.archive.suffixes).lower()
        return ext == ".zip"

    @property
    def _is_ar(self) -> bool:
        return self.archive.name.lower().endswith(".deb")

    @property
    def _is_gzip(self) -> bool:
        return not self._is_tar and self.archive.name.lower().endswith(".gz")
