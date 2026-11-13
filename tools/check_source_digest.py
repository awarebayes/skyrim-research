"""Scoped include-resolution caches for the repository check."""
from contextlib import contextmanager
from contextvars import ContextVar
import os
from pathlib import Path, PurePosixPath

from source_digest import INCLUDE_ROOTS, PRIVATE_DIRS, include_closure as reference_closure, quoted_includes


# A check sees one stable tree. Keep caches scoped to that operation, never across checks.
_CACHE = ContextVar('source_digest_cache', default=None)


@contextmanager
def source_digest_cache():
    token = _CACHE.set({'directories': {}, 'includes': {}, 'closures': {}})
    try:
        yield
    finally:
        _CACHE.reset(token)


def _directory_entries(path):
    cache = _CACHE.get()
    directories = cache['directories'] if cache is not None else None
    if directories is not None and path in directories:
        return directories[path]
    entries = os.listdir(path)
    folded = {}
    for entry in entries:
        folded.setdefault(entry.casefold(), []).append(entry)
    result = (set(entries), folded)
    if directories is not None:
        directories[path] = result
    return result


def _repo_file(root, rel):
    """`rel` normalised to a repository-relative POSIX path if it names an admissible file, else None."""
    norm = os.path.normpath(rel).replace(os.sep, '/')
    if norm in {'.', '..'} or norm.startswith('../') or os.path.isabs(norm) or '\\' in norm:
        return None
    parts = norm.split('/')
    if parts[0] in PRIVATE_DIRS:
        return None
    base = os.path.realpath(root)
    current = base
    for part in parts:
        try:
            entries, folded = _directory_entries(current)
        except OSError:
            return None
        # Exact spelling, and no sibling differing only in case that a Windows host could pick.
        if part not in entries or len(folded.get(part.casefold(), ())) != 1:
            return None
        current = os.path.join(current, part)
        if os.path.islink(current):
            return None
    real = os.path.realpath(current)
    inside = os.path.relpath(real, base).replace(os.sep, '/')
    if real != current or inside.startswith('../') or inside.split('/')[0] in PRIVATE_DIRS:
        return None
    return norm if os.path.isfile(real) else None


def _present_loosely(root, rel):
    """Whether something exists at `rel` under root when names are compared case-insensitively."""
    current = os.path.realpath(root)
    for part in os.path.normpath(rel).replace(os.sep, '/').split('/'):
        try:
            entries, folded = _directory_entries(current)
        except OSError:
            return False
        match = folded.get(part.casefold(), ())
        if not match:
            return False
        current = os.path.join(current, match[0])
    return True


def include_closure(root, compiled, roots=None):
    """Every repository file of the translation unit of `compiled`, sorted; see the module doc.

    `roots` replaces INCLUDE_ROOTS for one call. The match gate always uses the default; a narrower
    tuple lets a caller ask whether the unit still resolves with only the `/I` roots a given recipe
    passes, which is what the compiler will see.
    """
    if _CACHE.get() is None:
        return reference_closure(root, compiled, roots)
    roots = INCLUDE_ROOTS if roots is None else tuple(roots)
    root = Path(root)
    start = _repo_file(root, compiled)
    if start is None or start != PurePosixPath(compiled).as_posix():
        raise ValueError(f'compiled file {compiled} is not a repository-relative regular file')
    cache = _CACHE.get()
    closure_key = (os.path.abspath(root), start, roots)
    if cache is not None and closure_key in cache['closures']:
        return list(cache['closures'][closure_key])
    seen = {start}
    # The search path depends on who included a file, so each distinct includer chain is resolved;
    # a file already open in its own chain is a cycle stopped by its include guard.
    visited = set()
    stack = [(start, ())]
    while stack:
        name, chain = stack.pop()
        dirs = [PurePosixPath(name).parent] + [PurePosixPath(p).parent for p in reversed(chain)]
        key = (name, tuple(dict.fromkeys(dirs)))
        if key in visited:
            continue
        visited.add(key)
        include_key = (os.path.abspath(root), name, key[1], roots)
        resolved = cache['includes'].get(include_key) if cache is not None else None
        if resolved is None:
            resolved = []
            for kind, target in quoted_includes((root / name).read_bytes(), name):
                shown = f'"{target}"' if kind == '"' else f'<{target}>'
                # Angle includes search only the /I roots (then the toolchain), never the includer's directory.
                bases = (dirs if kind == '"' else []) + [PurePosixPath(r) for r in roots]
                if kind == '<' and (PurePosixPath(target).is_absolute() or '..' in PurePosixPath(target).parts):
                    raise ValueError(f'{name}: #include {shown} leaves the include roots')
                found = []
                if not PurePosixPath(target).is_absolute():
                    for base in bases:
                        hit = _repo_file(root, (base / target).as_posix())
                        if hit is not None and hit not in found:
                            found.append(hit)
                        elif hit is None and kind == '<' and _present_loosely(root, (base / target).as_posix()):
                            # A Windows host could still open it (other case, symlink), so it is not a
                            # toolchain header; the closure cannot bind it either.
                            raise ValueError(f'{name}: #include {shown} names a repository path that is not admissible')
                if kind == '<' and not found:
                    continue  # toolchain or SDK header, bound by the toolchain pin
                if len(found) != 1:
                    what = 'cannot be resolved inside the repository' if not found else f'is ambiguous ({", ".join(found)})'
                    raise ValueError(f'{name}: #include {shown} {what}')
                resolved.append(found[0])
            if cache is not None:
                cache['includes'][include_key] = tuple(resolved)
        for included in resolved:
            seen.add(included)
            if included != name and included not in chain:
                stack.append((included, chain + (name,)))
    result = sorted(seen)
    if cache is not None:
        cache['closures'][closure_key] = tuple(result)
    return result
