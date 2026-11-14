"""Private storage paths shared by contributor tools; SR_LOCAL_DIR must already exist."""
import os
from pathlib import Path


def local_dir(root, env=None):
    env = os.environ if env is None else env
    override = env.get('SR_LOCAL_DIR')
    if not override:
        return Path(root) / '.local'
    path = Path(override).expanduser()
    if not path.is_absolute():
        path = Path(root) / path
    if not path.is_dir():
        raise ValueError('SR_LOCAL_DIR must name an existing directory')
    return path.resolve()


def local_path(root, path, env=None):
    """Resolve repo-relative paths, relocating only paths under the default .local root."""
    path = Path(path)
    if not path.is_absolute() and path.parts[:1] == ('.local',):
        return local_dir(root, env) / Path(*path.parts[1:])
    return path if path.is_absolute() else Path(root) / path


def no_sibling_names(env=None):
    return (os.environ if env is None else env).get('SR_NO_SIBLING_NAMES') == '1'
