"""Process serialization and atomic files for the private pipeline state."""
from contextlib import contextmanager
from contextvars import ContextVar
import fcntl
import json
import os
from pathlib import Path
import tempfile


_HELD = ContextVar('flow_state_locks', default={})


@contextmanager
def state_lock(directory):
    """Serialize the complete read/modify/write operation, including group id allocation.

    The lock inode is permanent: unlinking it would let waiters lock different files.
    The OS releases the advisory lock when its owning process exits.
    """
    directory = Path(directory).resolve()
    key = (os.getpid(), str(directory))
    if key in _HELD.get():
        yield
        return
    directory.mkdir(parents=True, exist_ok=True)
    inherited = os.environ.get('SKYRIM_FLOW_LOCK_FD')
    if inherited and inherited.isdigit():
        fd = int(inherited)
        try:
            opened, expected = os.fstat(fd), (directory / '.state.lock').stat()
            same = (opened.st_dev, opened.st_ino) == (expected.st_dev, expected.st_ino)
        except OSError:
            same = False
        if same:
            fcntl.flock(fd, fcntl.LOCK_EX)
            token = _HELD.set(dict(_HELD.get()) | {key: fd})
            try:
                yield
            finally:
                _HELD.reset(token)
            return
    with (directory / '.state.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        token = _HELD.set(_HELD.get() | {key: handle.fileno()})
        try:
            yield
        finally:
            _HELD.reset(token)
            fcntl.flock(handle, fcntl.LOCK_UN)


def atomic_write(path, blob):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(blob)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def inherited_lock():
    return next(iter(_HELD.get().values()), None)


def require_complete(directory):
    for path in (Path(directory) / 'imports').glob('*.json'):
        if json.loads(path.read_text()).get('complete') is not True:
            raise ValueError('incomplete state import; resume import-state before any other flow operation')
