import errno
import hashlib
import os
import shutil
import tempfile


def sha256sum(filename):
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filename, "rb", buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()


def copy_file(src, dst):
    with tempfile.NamedTemporaryFile(
        prefix=src.name + ".", dir=dst.parent, delete=False
    ) as f:
        f.close()
        os.unlink(f.name)
        link_file(src, f.name)

        dst.unlink(missing_ok=True)
        os.rename(f.name, dst)


def link_file(src, dst):
    try:
        os.link(src, dst, follow_symlinks=False)
    except OSError as exc:
        if exc.errno != errno.EXDEV:
            raise
        else:
            shutil.copy2(src, dst, follow_symlinks=False)
