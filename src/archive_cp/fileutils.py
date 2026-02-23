"""Functions for operating on files."""
import errno
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple, TypeAlias
import zipfile


StrPath: TypeAlias = str | os.PathLike[str]
StrOrBytesPath: TypeAlias = str | bytes | os.PathLike[str] | os.PathLike[bytes]


def sha256sum(filename: StrOrBytesPath) -> str:
    """Return the SHA256 checksum of the specified file."""
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filename, "rb", buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()


def zip_chksum(
    source_file: Path, ignore_case: bool = False
) -> Tuple[Optional[str], Optional[str]]:
    """Return a checksum based upon zip file contents."""
    md5 = hashlib.md5()

    try:
        archive = zipfile.ZipFile(source_file)
    except zipfile.BadZipFile:
        return None, f"Bad zip file: {source_file}"

    for info in archive.infolist():
        fname = info.filename
        chkname = fname.lower() if ignore_case else fname
        md5.update(chkname.encode("utf-8"))
        md5.update(info.CRC.to_bytes(4, "big"))
        md5.update(str(info.date_time).encode("utf-8"))

    return md5.hexdigest(), None


def copy_file(src: Path, dst: Path) -> None:
    """Copy SRC to DST.

    DST is renamed into place to ensure the operation is atomic, using an
    intermediate temporary file.
    """
    with tempfile.NamedTemporaryFile(
        prefix=src.name + ".", dir=dst.parent, delete=False
    ) as f:
        f.close()
        os.unlink(f.name)
        link_file(src, f.name)

        dst.unlink(missing_ok=True)
        os.rename(f.name, dst)


def link_file(src: StrPath, dst: StrPath) -> None:
    """Link SRC to DST, copying if they cannot be linked."""
    try:
        os.link(src, dst, follow_symlinks=False)
    except OSError as exc:
        if exc.errno not in [errno.EXDEV, errno.ENOTSUP]:
            # cross-device link not permitted or operation not supported
            raise
        else:
            shutil.copy2(src, dst, follow_symlinks=False)
