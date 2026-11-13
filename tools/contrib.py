#!/usr/bin/env python3
"""Contributor helper: set up, claim a function, get its bytes from your own game, write C++,
compare locally and open a pull request. Python 3.11+ standard library only; Linux, macOS, Windows.

    python3 tools/contrib.py go [--profile cheap|full]   # one command: setup, pick, claim and start a function
    python3 tools/contrib.py doctor             # what is present, what is missing, the one next step
    python3 tools/contrib.py setup [--yes] [--exe PATH] [--accept-microsoft-license]
    python3 tools/contrib.py next               # easy unclaimed functions
    python3 tools/contrib.py claim 0x<rva>      # GitHub issue as a claim (or a prefilled link)
    python3 tools/contrib.py start 0x<rva>      # branch, unit skeleton, local pack from your exe
    python3 tools/contrib.py compare            # compile with the pinned MSVC and run the comparator
    python3 tools/contrib.py submit [--dry-run] # checks, commit, push, pull request
    python3 tools/contrib.py release 0x<rva>    # give a claim back
    python3 tools/contrib.py intake --base REF  # contributor-scope checks of a diff (CI, maintainers)

Every command takes --json (one JSON object on stdout) and never prompts when stdin is not a
terminal or --json is given: a step that needs a person exits 7 and names the flag to pass.
Exit codes: 0 ok, 1 a check failed (compare or lint), 2 usage or internal error, 3 compile failed,
4 unit or include problem, 5 a required input is missing (game executable, toolchain), 6 the
function is claimed by someone else, 7 a person must decide (licence, path, install), 8 network
needed but unavailable.

Nothing here uploads game-derived material. The executable is read where it is installed; packs,
objects, listings and reports stay under the ignored `.local/contrib/`. A pull request carries
source files and a sanitized comparator summary only. A local pass is not acceptance: the project
re-runs the comparison on two of its own hosts and a Reviewer checks the source before anything is
recorded as `matched` (docs/verification.md).

`--profile` (on `go` and `start`; remembered in the private config) chooses what your coding agent
reads and how many compare runs it tries before stopping: `cheap` (default; small card, for
Haiku- or Luna-class models) or `full` (full card and cookbook, for Sonnet-class models). It never
changes what counts as a match. `python3 tools/profiles.py` prints a rough cost line for each.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import ntpath
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shlex
import shutil
import struct
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

import profiles

REPO = Path(__file__).resolve().parents[1]
TOOLS = REPO / 'tools'
for _p in (TOOLS, TOOLS / 'verifier', TOOLS / 'analysis', TOOLS / 'ghidra'):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

OK, FAILED, USAGE, COMPILE, UNIT, MISSING, CLAIMED, CONSENT, NETWORK = 0, 1, 2, 3, 4, 5, 6, 7, 8
UPSTREAM = 'awarebayes/skyrim-research'
COMPILE_TIMEOUT = 180
# Contributor units are small; a cap keeps a pathological file away from the compiler and reviewers.
MAX_UNIT_FILE_BYTES = 64 * 1024
DEFAULT_RECIPE = 'reconstruction/recipes/msvc-19.16.27054-o2.json'
# A matched function with a two-file unit, used by `setup` to prove the whole local chain works.
SELF_TEST_RVA = 0xef8900
UNIT_PATH = re.compile(r'reconstruction/([a-z][a-z0-9_]*)/([A-Z][A-Za-z0-9_]*)\.(h|cpp)')
PLAIN_NAME = re.compile(r'([A-Z][A-Za-z0-9_]*)::(~?[A-Za-z_][A-Za-z0-9_]*)')
RVA_TOKEN = re.compile(r'(?<![0-9A-Za-z])0x([0-9a-fA-F]{3,8})(?![0-9A-Za-z])')
# Pinned community naming sources (SOURCES.md) that tools/check_labels.py and check_origin.py read
# from .local/sources/.
COMMUNITY_SOURCES = {
    'CharmedBaryon/CommonLibSSE-NG': ('.local/sources/CommonLibSSE-NG', 'b93280e832f263dbef44e44cbe2936622a02f91a', 'MIT'),
    'powerof3/CommonLibSSE': ('.local/sources/CommonLibSSE-po3', '654e55f7979c1733033d5dbef176e43827bac944', 'GPL-3.0'),
    'meh321/AddressLibraryDatabase': ('.local/sources/AddressLibraryDatabase', '0379cb6fdaa0d68e69ef9ad1a2d39caa6611ac91',
                                      'permission'),
}
# The FNV decompilation, readable and reusable by contributors on the same terms as the project's
# Drafters (docs/authorizations.md, Notes; LEGAL.md): SIBLING(...) labels, a `Sibling source:` line
# for a reused body, never evidence about the Skyrim binary. Optional: setup skips it with
# --no-sibling, and nothing else depends on it.
SIBLING_SOURCE = ('momusdigital/fnv_decomp', '.local/sources/fnv_decomp', '91e1b6e8d8bb0f9a33e8cf88e77268757449e0a6')
# Steam ids. The app and build ids come from findings/target-pin.md; the depot and manifest of the
# executable are recorded from the maintainer's own install (its appmanifest lists them, and its
# build id equals the pin). Steam may move the app to a newer build at any time, which is why the
# executable is always checked against the pinned SHA-256 after a download.
STEAM_APP_ID = '489830'
STEAM_BUILD_ID = '24914197'
STEAM_EXE_DEPOT = '489833'
STEAM_EXE_MANIFEST = '4886117324142477814'
# Homebrew disabled its Wine casks (they fail Gatekeeper), so on macOS this tool fetches WineHQ's
# build as packaged by Gcenx, the same archive and hash his tap's wine-stable cask names.
CONTRIB_PROFILES = ('cheap', 'full')
MAC_WINE = {'version': '11.0_1', 'app': 'Wine Stable.app',
            'url': 'https://github.com/Gcenx/macOS_Wine_builds/releases/download/11.0_1/wine-stable-11.0_1-osx64.tar.xz',
            'sha256': 'b50dc50ec7f41d58b115a6b685d4d1315ba3c797bd3aa0f49213f2703cb82388'}


class Stop(Exception):
    """End a command with an exit code, a message and the one next action."""

    def __init__(self, code, message, next_action=None, **data):
        super().__init__(message)
        self.code, self.message, self.next_action, self.data = code, message, next_action, data


# ------------------------------------------------------------------ context and output

class Ctx:
    """Everything a command reads from its surroundings, so tests can substitute any of it."""

    def __init__(self, repo=REPO, env=None, platform=None, interactive=None, as_json=False, assume_yes=False,
                 runner=None, github=None, private=None):
        self.repo = Path(repo)
        self.env = dict(os.environ if env is None else env)
        self.platform = platform or sys.platform
        if interactive is None:
            interactive = sys.stdin.isatty() and sys.stdout.isatty()
        self.interactive = bool(interactive) and not as_json
        self.as_json, self.assume_yes = as_json, assume_yes
        self.private = Path(private) if private else self.repo / '.local' / 'contrib'
        self.runner = runner or subprocess.run
        self._github = github
        self.log = []
        self.redact = False

    @property
    def windows(self):
        return self.platform == 'win32'

    @property
    def cli(self):
        # sr.cmd names itself: a newcomer it bootstrapped has no `py` launcher on PATH.
        if self.windows and self.env.get('SR_LAUNCHER') == '.\\sr.cmd':
            return '.\\sr.cmd'
        return 'py tools\\contrib.py' if self.windows else 'python3 tools/contrib.py'

    def which(self, name):
        return shutil.which(name, path=self.env.get('PATH'))

    def run(self, cmd, **kw):
        kw.setdefault('env', self.env)
        return self.runner(cmd, **kw)

    def scrub(self, text):
        """With --redact, the checkout and home paths replaced, for output meant to be posted."""
        if not self.redact:
            return text
        home = self.env.get('USERPROFILE' if self.windows else 'HOME') or str(Path.home())
        for path, mark in ((str(self.repo), '<repo>'), (home, '~')):
            if path and len(path) > 1:
                text = text.replace(path, mark).replace(path.replace('\\', '\\\\'), mark)
                if self.windows or self.platform == 'darwin':
                    text = re.sub(re.escape(path), mark, text, flags=re.I)
        return text

    def say(self, line):
        line = self.scrub(line)
        self.log.append(line)
        if not self.as_json:
            print(line, flush=True)

    def ask(self, question, flag):
        """Yes/no from a person; never asks without a terminal (exit 7 naming the flag instead)."""
        if self.assume_yes:
            return True
        if not self.interactive:
            raise Stop(CONSENT, f'{question} (no terminal to ask on)', f'rerun with {flag} once a person has agreed')
        answer = input(f'{question} [y/N] ').strip().lower()
        return answer in ('y', 'yes')

    def github(self):
        if self._github is None:
            self._github = GitHub(self)
        return self._github


def config_path(ctx):
    return ctx.private / 'config.json'


def load_config(ctx):
    try:
        return json.loads(config_path(ctx).read_text())
    except (OSError, ValueError):
        return {}


def save_config(ctx, **changes):
    cfg = load_config(ctx)
    cfg.update(changes)
    config_path(ctx).parent.mkdir(parents=True, exist_ok=True)
    config_path(ctx).write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')
    return cfg


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def target_manifest(repo):
    return json.loads((Path(repo) / 'builds/target.json').read_text())


def parse_rva(text):
    if isinstance(text, int):
        return text
    m = re.fullmatch(r'(?:0x)?([0-9a-fA-F]+)', str(text).strip())
    if not m:
        raise Stop(USAGE, f'not an RVA: {text!r} (write it as 0x<hex>)')
    return int(m.group(1), 16)


def git(ctx, *args, check=True, cwd=None):
    proc = ctx.run(['git', *args], cwd=cwd or ctx.repo, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise Stop(USAGE, f'git {" ".join(args)} failed: {proc.stderr.strip()[:300]}')
    return proc.stdout.strip()


# ------------------------------------------------------------------ inventory

def inventory(repo):
    return json.loads((Path(repo) / 'data/progress.json').read_text())


def find_function(data, rva):
    for fn in data['functions']:
        if fn['rva'] == rva:
            return fn
    return None


def community_label(name_source):
    """The COMMUNITY(...) label an inventory entry's name source supports, and its licence word."""
    text = name_source or ''
    for repo, (_path, rev, licence) in COMMUNITY_SOURCES.items():
        if repo in text:
            return f'COMMUNITY({repo}@{rev[:7]}, {licence})', licence
    return None, None


def area_for(cls):
    try:
        from export_pack import area_for as rule
    except Exception:  # noqa: BLE001 - the rule is optional; a missing area is asked for instead
        return None
    return rule(cls)


def unit_files(repo, cls, area=None):
    """(area, .h, .cpp) repository paths of the class's unit, existing or proposed."""
    for path in sorted((Path(repo) / 'reconstruction').glob(f'*/{cls}.cpp')):
        a = path.parent.name
        return a, f'reconstruction/{a}/{cls}.h', f'reconstruction/{a}/{cls}.cpp'
    area = area or area_for(cls)
    if area is None:
        return None, None, None
    return area, f'reconstruction/{area}/{cls}.h', f'reconstruction/{area}/{cls}.cpp'


def candidates(repo, data, claimed=(), max_size=None):
    """Mapped functions a newcomer can start on, cheapest first: classes without a unit (no accepted
    function goes stale), an area the layout rule knows, a plain Class::Method name, small size."""
    out = []
    for fn in data['functions']:
        if fn['status'] != 'mapped' or fn['rva'] in claimed:
            continue
        if max_size and fn['size'] > max_size:
            continue
        m = PLAIN_NAME.fullmatch(fn.get('name') or '')
        cls = m.group(1) if m else None
        area, _h, cpp = unit_files(repo, cls) if cls else (None, None, None)
        has_unit = bool(cpp and (Path(repo) / cpp).is_file())
        out.append({'rva': f'0x{fn["rva"]:x}', 'size': fn['size'], 'name': fn.get('name'),
                    'name_origin': fn.get('name_origin'), 'unit': cpp, 'unit_exists': has_unit,
                    'startable': bool(m and area),
                    '_key': (not m or area is None, has_unit, fn['size'], fn['rva'])})
    out.sort(key=lambda c: c.pop('_key'))
    return out


# ------------------------------------------------------------------ the game executable

def pe_version(path):
    """FileVersion from the VS_FIXEDFILEINFO block of a PE file, or None."""
    try:
        blob = Path(path).read_bytes()
    except OSError:
        return None
    i = blob.find(b'\xbd\x04\xef\xfe')
    if i < 0 or i + 16 > len(blob):
        return None
    ms, ls = struct.unpack_from('<II', blob, i + 8)
    return f'{ms >> 16}.{ms & 0xffff}.{ls >> 16}.{ls & 0xffff}'


def steam_libraries(ctx, exists=os.path.isdir, read=None):
    """Steam library folders this machine has, from the usual Steam roots and libraryfolders.vdf."""
    home = ctx.env.get('USERPROFILE' if ctx.windows else 'HOME') or str(Path.home())
    if ctx.windows:
        P = PureWindowsPath
        roots = [P(ctx.env.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Steam',
                 P(ctx.env.get('ProgramFiles', r'C:\Program Files')) / 'Steam']
    else:
        P = PurePosixPath
        roots = [P(home) / '.steam/steam', P(home) / '.local/share/Steam',
                 P(home) / '.var/app/com.valvesoftware.Steam/.local/share/Steam',
                 P(home) / 'Library/Application Support/Steam', P(home) / 'Steam']
    read = read or (lambda p: Path(p).read_text(errors='replace'))
    libs = []
    for root in roots:
        if not exists(str(root)):
            continue
        libs.append(root)
        vdf = root / 'steamapps' / 'libraryfolders.vdf'
        try:
            text = read(str(vdf))
        except OSError:
            continue
        for m in re.finditer(r'"path"\s+"((?:[^"\\]|\\.)*)"', text):
            libs.append(P(m.group(1).replace('\\\\', '\\')))
    return list(dict.fromkeys(libs))


def exe_candidates(ctx, exists=os.path.isfile, dir_exists=os.path.isdir, read=None):
    found = []
    for lib in steam_libraries(ctx, dir_exists, read):
        p = lib / 'steamapps' / 'common' / 'Skyrim Special Edition' / 'SkyrimSE.exe'
        if exists(str(p)):
            found.append(str(p))
    # The SteamCMD route installs into .local/contrib/game; its depot-only variant writes under
    # SteamCMD's own steamapps/content folder.
    own = [ctx.private / 'game' / 'SkyrimSE.exe']
    own += [d / 'steamapps' / 'content' / f'app_{STEAM_APP_ID}' / f'depot_{STEAM_EXE_DEPOT}' / 'SkyrimSE.exe'
            for d in steamcmd_dirs(ctx)]
    for p in own:
        if exists(str(p)):
            found.append(str(p))
    return list(dict.fromkeys(found))


def inspect_exe(path, target):
    p = Path(path)
    if not p.is_file():
        return {'status': 'missing', 'path': str(path)}
    digest = sha256_file(p)
    return {'status': 'ok' if digest == target['image_sha256'] else 'wrong-build', 'path': str(p),
            'sha256': digest, 'version': pe_version(p)}


def wrong_build_message(info, target):
    return (f'{info["path"]} is version {info.get("version") or "unknown"} (SHA-256 {info["sha256"][:16]}...), '
            f'not the pinned target {target["version"]} from {target["store"]} '
            f'(SHA-256 {target["image_sha256"][:16]}...). The comparator needs exactly that file; '
            'see docs/contributing-agent.md, "The game executable".')


def steamcmd_route(ctx):
    """The official SteamCMD steps for the contributor's own account; credentials are typed into
    SteamCMD by the contributor and never pass through this tool."""
    where = ctx.private / 'game'
    return ['steamcmd   (then type these at its Steam> prompt; it asks for your password itself)',
            '@sSteamCmdForcePlatformType windows',
            f'force_install_dir "{where}"',
            'login <your-steam-login>',
            f'app_update {STEAM_APP_ID} validate      (whole game, about 13 GB; the route the maintainer used)',
            f'  or: download_depot {STEAM_APP_ID} {STEAM_EXE_DEPOT} {STEAM_EXE_MANIFEST}      (only the executable, '
            'about 38 MB; not yet tried by the project; SteamCMD prints the folder it wrote)',
            'quit',
            f'then: {ctx.cli} setup      (it looks in both places; or pass --exe "<path to SkyrimSE.exe>")']


def steamcmd_dirs(ctx):
    """Where SteamCMD keeps its own files on this platform (its depot downloads land beneath)."""
    home = Path(ctx.env.get('USERPROFILE' if ctx.windows else 'HOME') or str(Path.home()))
    if ctx.windows:
        return [Path(r'C:\steamcmd')]
    return [home / 'Library/Application Support/Steam', home / '.steam/steamcmd', home / '.steam/steam',
            home / '.local/share/Steam', home / 'Steam', Path('/usr/games/steamcmd')]


def resolve_exe(ctx, target, given=None):
    """(info, how) for the configured or discovered executable; info None when nothing is found."""
    cfg = load_config(ctx)
    for how, path in (('--exe', given), ('SR_SKYRIM_EXE', ctx.env.get('SR_SKYRIM_EXE')), ('config', cfg.get('exe'))):
        if path:
            return inspect_exe(path, target), how
    infos = [inspect_exe(p, target) for p in exe_candidates(ctx)]
    good = [i for i in infos if i['status'] == 'ok']
    if good:
        return good[0], 'found in a Steam library'
    if infos:
        return infos[0], 'found in a Steam library'
    return None, None


def require_exe(ctx, target):
    info, _how = resolve_exe(ctx, target)
    if info is None or info['status'] == 'missing':
        raise Stop(MISSING, 'SkyrimSE.exe not configured or not found', f'{ctx.cli} setup --exe "<path to SkyrimSE.exe>"')
    if info['status'] != 'ok':
        raise Stop(MISSING, wrong_build_message(info, target), f'{ctx.cli} doctor')
    return info


# ------------------------------------------------------------------ toolchain

def recipe_constants(repo):
    """Pins of the verifier toolchain recipe, read through the shared accessor so the contributor
    path cannot drift from the recipe the project's verifiers use."""
    import recipe_pins
    try:
        return recipe_pins.read_pins(repo)
    except recipe_pins.MissingPin as exc:
        raise Stop(USAGE, str(exc))


def pinned_hashes(repo):
    out = {}
    for line in (Path(repo) / 'tools/verifier/pinned.sha256').read_text().splitlines():
        parts = line.split()
        if len(parts) == 2:
            out[parts[1]] = parts[0]
    return out


def toolchain_root(ctx):
    cfg = load_config(ctx)
    return Path(ctx.env.get('SR_MSVC') or cfg.get('msvc') or ctx.private / 'msvc')


def toolchain_bins(root):
    return sorted(Path(root).glob('VC/Tools/MSVC/*/bin/Hostx64/x64'))


def sdk_include_dirs(ctx, root, sdk_version):
    """Windows SDK include directories for a native compile (the msvc-wine wrapper sets its own)."""
    bases = [Path(root) / 'Windows Kits' / '10' / 'Include',
             Path(ctx.env.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Windows Kits' / '10' / 'Include']
    for base in bases:
        versions = sorted(p for p in base.glob('10.*') if p.is_dir()) if base.is_dir() else []
        pick = [p for p in versions if p.name.startswith(sdk_version)] or versions[-1:]
        if pick:
            return base.parent.parent.parent, [pick[0] / d for d in ('ucrt', 'shared', 'um', 'winrt')]
    return None, []


def check_toolchain(ctx):
    """State of the compiler: 'override' (a test stand-in), 'ok', 'missing', 'mismatch' or 'no-wrapper'."""
    override = ctx.env.get('SR_CONTRIB_COMPILER')
    if override:
        return {'status': 'override', 'command': json.loads(override) if override.startswith('[') else [override],
                'pinned': False}
    root = toolchain_root(ctx)
    bins = toolchain_bins(root)
    if not bins:
        return {'status': 'missing', 'root': str(root), 'pinned': False}
    pins = pinned_hashes(ctx.repo)
    bad = [name for name, digest in pins.items()
           if not (bins[-1] / name).is_file() or sha256_file(bins[-1] / name) != digest]
    info = {'root': str(root), 'bin': str(bins[-1]), 'pinned': not bad, 'flavour': 'native' if ctx.windows else 'wine'}
    if bad:
        return dict(info, status='mismatch', differing=bad)
    if not ctx.windows and not (root / 'bin' / 'x64' / 'cl').is_file():
        return dict(info, status='no-wrapper')
    return dict(info, status='ok')


# ------------------------------------------------------------------ compiling a unit

def classify_windows(opened, repo, tool_roots):
    """Split /showIncludes paths of a native Windows compile into repository files (exact spelling,
    POSIX form), a toolchain count and anything else."""
    def norm(p):
        return ntpath.normpath(str(p).replace('/', '\\'))
    repo_n = norm(repo)
    roots = [norm(r).lower().rstrip('\\') + '\\' for r in tool_roots if r]
    files, outside, tools = set(), [], 0
    for raw in opened:
        p = norm(raw)
        low = p.lower()
        if any(low.startswith(r) for r in roots):
            tools += 1
        elif low.startswith(repo_n.lower().rstrip('\\') + '\\') and '\\..' not in low:
            files.add(p[len(repo_n.rstrip('\\')) + 1:].replace('\\', '/'))
        else:
            outside.append(raw)
    return sorted(files), tools, outside


def compile_unit(ctx, root, compiled, recipe_rel, out_dir, tool):
    """Compile one unit with the recipe's flags and the build-path checks of the verifier
    (tools/verifier/unit_build.py): cleared environment, /showIncludes equal to the closure."""
    import unit_build
    from source_digest import include_closure, recipe_flag_problem, tu_digest
    # The compiler reports opened files from the real working directory, so compare against that.
    root, out_dir = Path(root).resolve(), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        closure = include_closure(root, compiled)
    except (ValueError, OSError) as exc:
        raise Stop(UNIT, f'translation unit: {exc}', 'fix the include named above; docs/drafter-card.md, "Source rules"')
    recipe_bytes = (root / recipe_rel).read_bytes()
    recipe = json.loads(recipe_bytes)
    problem = recipe_flag_problem(recipe.get('flags'))
    if problem:
        raise Stop(UNIT, f'recipe flags: {problem}')
    env = unit_build.clean_env(ctx.env)
    env.update(VSLANG='1033', WINEDEBUG='-all')  # English /showIncludes notes; quiet Wine
    obj = out_dir / 'candidate.obj'
    if obj.exists():
        obj.unlink()
    status = tool['status']
    if status == 'override':
        cmd, roots, flavour = list(tool['command']), [], 'override'
    elif status != 'ok':
        raise Stop(MISSING, f'compiler toolchain is {status}', f'{ctx.cli} setup')
    elif tool['flavour'] == 'wine':
        msvc = Path(tool['root'])
        wrapper = unit_build.wrapper_settings(msvc, env)
        problem = unit_build.include_problem(wrapper['INCLUDE'], wrapper['BASE'])
        if problem:
            raise Stop(UNIT, problem)
        cmd, roots, flavour = [str(msvc / 'bin/x64/cl')], [wrapper['BASE'][2:].replace('\\', '/')], 'wine'
    else:
        sdk_root, includes = sdk_include_dirs(ctx, tool['root'], recipe_constants(ctx.repo)['SDK_VERSION'])
        vc_include = Path(tool['bin']).parents[2] / 'include'
        env['INCLUDE'] = ';'.join(str(p) for p in [vc_include, *includes])
        cmd, roots, flavour = [str(Path(tool['bin']) / 'cl.exe')], [tool['root'], sdk_root], 'native'
    cmd = cmd + recipe['flags'] + [unit_build.SHOW_INCLUDES, f'/Fo{obj}', compiled]
    try:
        proc = ctx.run(cmd, cwd=root, env=env, capture_output=True, text=True, errors='replace',
                       timeout=COMPILE_TIMEOUT)
    except subprocess.TimeoutExpired:
        raise Stop(COMPILE, f'compile took longer than {COMPILE_TIMEOUT} s and was stopped')
    except OSError as exc:
        raise Stop(MISSING, f'cannot run the compiler: {exc}', f'{ctx.cli} doctor')
    opened, rest = unit_build.parse_show_includes(proc.stdout)
    (out_dir / 'compile.log').write_text('\n'.join(rest) + '\n' + (proc.stderr or ''))
    if proc.returncode != 0 or not obj.is_file():
        errors = [line.strip() for line in rest if re.search(r'\berror [A-Z]+\d+', line)][:8]
        raise Stop(COMPILE, 'compile failed', 'fix the errors and run compare again',
                   errors=errors, log=str(out_dir / 'compile.log'))
    if flavour == 'native':
        repo_files, tool_count, outside = classify_windows(opened, root, roots)
    else:
        repo_files, tool_count, outside = unit_build.classify_includes(opened, root, Path(roots[0]) if roots
                                                                       else Path('/nonexistent-toolchain'))
    if outside and ctx.platform == 'darwin':
        outside = fold_case_includes(outside, root, closure, repo_files)
    if outside:
        raise Stop(UNIT, f'{len(outside)} included file(s) outside the repository and the toolchain: '
                   + ', '.join(outside[:3]), 'include only reconstruction/ headers and the toolchain\'s own',
                   outside=outside[:20])
    diff = unit_build.closure_difference(repo_files, compiled, closure)
    if diff:
        raise Stop(UNIT, diff, 'move or remove the include named above')
    digest = tu_digest(root, closure)
    recipe_sha = hashlib.sha256(recipe_bytes).hexdigest()
    record = {'build_record_schema': 1, 'source_revision': digest, 'source_path': compiled,
              'recipe_sha256': recipe_sha, 'object_sha256': sha256_file(obj),
              'environment': {'cleared': list(unit_build.CLEARED_ENV), 'added_flags': [unit_build.SHOW_INCLUDES],
                              'compiler': flavour, 'toolchain_files': tool_count}}
    (out_dir / 'build-record.json').write_text(json.dumps(record, indent=2) + '\n')
    return {'object': obj, 'closure': closure, 'digest': digest, 'recipe_sha256': recipe_sha,
            'build_record': out_dir / 'build-record.json', 'compiler': flavour}


def fold_case_includes(outside, root, closure, repo_files):
    """Entries of `outside` that are closure files spelled in another case, moved into repo_files.

    macOS volumes are usually case-insensitive and Wine there may report an opened header in lower
    case. Only an exact case-insensitive match to a file of the derived closure is accepted, and
    only when the reported path opens that very file (same device and inode), so a file outside the
    repository, or a different file whose name merely folds to a closure name, still fails."""
    prefix = str(root).rstrip('/').lower() + '/'
    by_lower = {c.lower(): c for c in closure}
    rest = []
    for raw in outside:
        path = raw.replace('\\', '/')
        if len(path) > 2 and path[1] == ':':
            path = path[2:]
        hit = by_lower.get(path.lower()[len(prefix):]) if path.lower().startswith(prefix) else None
        if hit and '/../' not in path and same_file(path, os.path.join(str(root), hit)):
            if hit not in repo_files:
                repo_files.append(hit)
        else:
            rest.append(raw)
    repo_files.sort()
    return rest


def same_file(a, b):
    """True when both paths open one existing file; a missing or unreadable path is not a match."""
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


# ------------------------------------------------------------------ the local pack

def public_names(repo, data):
    """{rva: [names]} from the public symbol map and the inventory, for reading a listing."""
    from bind import fallback_qualified
    names = {}
    target = target_manifest(repo)
    smap = Path(repo) / 'reports' / target['build_id'] / 'symbol-map.json'
    if smap.is_file():
        for name, entry in json.loads(smap.read_text()).get('symbols', {}).items():
            if isinstance(entry, dict) and isinstance(entry.get('rva'), int):
                names.setdefault(entry['rva'], []).append(fallback_qualified(name) or name)
    for fn in data['functions']:
        if fn.get('name'):
            names.setdefault(fn['rva'], []).insert(0, fn['name'])
    return {k: list(dict.fromkeys(v)) for k, v in names.items()}


def build_pack(image_bytes, rva, size, identity, names):
    """Pack of one function from the image: its bytes, instruction boundaries and the targets of its
    calls, jumps and rip-relative references with any public name. Private (game-derived)."""
    from pecoff import PeImage
    import x64
    image = PeImage(image_bytes)
    _sec, code = image.read(rva, size, 'function')
    rows, refs, note = [], {}, None
    try:
        insns = x64.decode_range(code, 0, size, rva)
    except x64.DecodeError as exc:
        insns, note = [], f'instruction decoding stopped: {exc}'
    for off, ins in insns:
        field, target, kind = None, None, None
        if ins.rel is not None and not (rva <= ins.target < rva + size):
            field, target, kind = ins.rel, ins.target, 'call-or-jump'
        elif ins.rip is not None:
            field, target, kind = (ins.rip, 4), ins.rip_target, 'data-or-code'
        rows.append({'offset': off, 'length': ins.length, 'field': field, 'target': target})
        if target is not None:
            r = refs.setdefault(target, {'target_rva': target, 'kind': kind, 'at': [],
                                         'community_names': [{'name': n, 'kind': 'name'} for n in names.get(target, [])]})
            r['at'].append(off + field[0])
    pdata = [e for e in image.runtime_functions() if rva <= e[0] < rva + size]
    return {'pack_schema': 1, 'source': 'local-exe', 'identity': dict(identity, name_how=None),
            'bytes_hex': code.hex(), 'instructions': rows, 'references': list(refs.values()),
            'unwind_entries': len(pdata), 'note': note}


def pack_listing(pack):
    """A readable byte listing: offset, bytes (relocated fields as ..) and reference targets."""
    code = bytes.fromhex(pack['bytes_hex'])
    lines = [f'# {pack["identity"].get("community_name")} RVA 0x{pack["identity"]["rva"]:x} '
             f'{pack["identity"]["size"]} bytes; private, never paste or upload']
    for row in pack['instructions']:
        raw = code[row['offset']:row['offset'] + row['length']]
        cells = [f'{b:02x}' for b in raw]
        if row['field']:
            for i in range(row['field'][0], row['field'][0] + row['field'][1]):
                cells[i] = '..'
        text = f'  +0x{row["offset"]:03x}  {" ".join(cells):<45}'
        if row['target'] is not None:
            ref = next(r for r in pack['references'] if r['target_rva'] == row['target'])
            names = ', '.join(c['name'] for c in ref['community_names'][:2]) or 'no public name'
            text += f' -> 0x{row["target"]:x} {names}'
        lines.append(text.rstrip())
    if pack.get('note'):
        lines.append(f'# {pack["note"]}')
    return '\n'.join(lines) + '\n'


def find_objdump(ctx):
    for name in (ctx.env.get('SR_OBJDUMP'), 'llvm-objdump', '/opt/homebrew/opt/llvm/bin/llvm-objdump',
                 '/usr/local/opt/llvm/bin/llvm-objdump', r'C:\Program Files\LLVM\bin\llvm-objdump.exe'):
        if name and (ctx.which(name) or os.path.isfile(name)):
            return ctx.which(name) or name
    return None


def write_pack(ctx, exe, fn, names):
    rva, size = fn['rva'], fn['size']
    dest = ctx.private / 'packs' / fn['build_id'] / f'0x{rva:x}'
    dest.mkdir(parents=True, exist_ok=True)
    identity = {'build_id': fn['build_id'], 'rva': rva, 'size': size, 'community_name': fn.get('name'),
                'name_origin': fn.get('name_origin')}
    pack = build_pack(Path(exe).read_bytes(), rva, size, identity, names)
    (dest / 'pack.json').write_text(json.dumps(pack, indent=1) + '\n')
    (dest / 'bytes.txt').write_text(pack_listing(pack))
    objdump = find_objdump(ctx)
    if objdump:
        import disasm
        try:
            rows = disasm.target_rows(objdump, exe, rva, size)
            # The `+0x.. MNEMONIC operands` form is what tools/verifier/bind.py reads for destructors.
            (dest / 'listing.txt').write_text(''.join(f'  +0x{r[0]:03x}  {r[2].upper()}\n' for r in rows))
        except (OSError, ValueError, subprocess.SubprocessError):
            pass
    return dest, pack


import claims as batch_claims  # noqa: E402


# ------------------------------------------------------------------ GitHub claims

class Offline(Exception):
    pass


class GitHub:
    """Open issues and pull requests of the upstream repository, through `gh` when it is signed in,
    else the public REST API (read only); creating a claim without `gh` gives a prefilled link."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.repo = ctx.env.get('SR_UPSTREAM') or UPSTREAM
        self._gh = None

    def gh(self):
        if self._gh is None:
            exe = self.ctx.which('gh')
            ok = bool(exe) and self.ctx.run([exe, 'auth', 'status'], capture_output=True, text=True).returncode == 0
            self._gh = exe if ok else False
        return self._gh or None

    def api(self, path):
        if self.ctx.env.get('SR_CONTRIB_OFFLINE'):
            raise Offline('offline mode (SR_CONTRIB_OFFLINE)')
        gh = self.gh()
        if gh:
            proc = self.ctx.run([gh, 'api', path], capture_output=True, text=True)
            if proc.returncode != 0:
                raise Offline(proc.stderr.strip()[:200])
            return json.loads(proc.stdout)
        req = urllib.request.Request(f'https://api.github.com/{path}', headers={
            'Accept': 'application/vnd.github+json', 'User-Agent': 'skyrim-research-contrib'})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read())
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise Offline(str(exc)) from None

    # Enough pages for any plausible number of open items; past it the list is reported incomplete
    # rather than silently treated as complete.
    MAX_PAGES = 100

    def open_items(self, refresh=False):
        """Open issues and pull requests whose title names an RVA: {rva: [item]}."""
        if getattr(self, '_items', None) is not None and not refresh:
            return self._items
        items = []
        for page in range(1, self.MAX_PAGES + 1):
            batch = self.api(f'repos/{self.repo}/issues?state=open&per_page=100&page={page}')
            if page == self.MAX_PAGES and len(batch) == 100:
                raise Offline(f'more than {100 * self.MAX_PAGES} open items; claims cannot all be checked')
            for it in batch:
                parsed = batch_claims.parse_issue(it)
                if parsed['entries']:
                    it['updated_at'] = batch_claims.activity(self.api, self.repo, it)
                    items.append(batch_claims.parse_issue(it))
            if len(batch) < 100:
                break
        out = batch_claims.ClaimIndex(items)
        self._items = out
        return out

    def user(self):
        cfg = load_config(self.ctx)
        if self.ctx.env.get('SR_GITHUB_USER') or cfg.get('github_user'):
            return self.ctx.env.get('SR_GITHUB_USER') or cfg['github_user']
        gh = self.gh()
        if gh:
            proc = self.ctx.run([gh, 'api', 'user', '-q', '.login'], capture_output=True, text=True)
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()
        return None

    def create_issue(self, title, body):
        gh = self.gh()
        if not gh:
            return None
        if len(body) >= batch_claims.BODY_LIMIT:
            raise Stop(USAGE, 'refusing issue body at or above 60,000 characters')
        label = self.ctx.run([gh, 'label', 'create', 'claim', '--repo', self.repo, '--color', '1d76db',
                              '--description', 'Function work claims', '--force'], capture_output=True, text=True)
        if label.returncode:
            raise Stop(NETWORK, 'cannot create or verify the claim label')
        me = self.user()
        if not me:
            raise Stop(USAGE, 'GitHub login is unknown')
        proc = self.ctx.run([gh, 'issue', 'create', '--repo', self.repo, '--title', title,
                             '--body-file', '-', '--label', 'claim', '--assignee', me],
                            input=body, capture_output=True, text=True)
        if proc.returncode == 0:
            return proc.stdout.strip().splitlines()[-1]
        raise Stop(NETWORK, 'gh issue create failed')

    def new_issue_link(self, title, body):
        q = urllib.parse.urlencode({'template': 'claim.yml', 'title': title, 'body': body})
        return f'https://github.com/{self.repo}/issues/new?{q}'

    def comment(self, number, body):
        gh = self.gh()
        if gh:
            self.ctx.run([gh, 'issue', 'comment', str(number), '--repo', self.repo, '--body', body],
                         capture_output=True, text=True)
            return True
        return False

    def close(self, number, body):
        gh = self.gh()
        if gh:
            self.ctx.run([gh, 'issue', 'close', str(number), '--repo', self.repo, '--comment', body],
                         capture_output=True, text=True)
            return True
        return False


def issue_number(url):
    m = re.search(r'/(?:issues|pull)/(\d+)', url or '')
    return int(m.group(1)) if m else 1 << 62


def claim_state(items, me, now=None):
    """Split claims on one function into mine, fresh claims by others and lapsed ones."""
    now = now or datetime.now(timezone.utc)
    mine, fresh, stale = [], [], []
    for it in items:
        if me and me in (it.get('assignees') or [it.get('author')]):
            mine.append(it)
            continue
        try:
            updated = datetime.fromisoformat(str(it.get('updated_at')).replace('Z', '+00:00'))
        except ValueError:
            updated = now
        (stale if now - updated >= batch_claims.CLAIM_LAPSE else fresh).append(it)
    return mine, fresh, stale


def local_claims(ctx):
    try:
        return json.loads((ctx.private / 'claims.json').read_text())
    except (OSError, ValueError):
        return {}


def save_local_claim(ctx, rva, record):
    claims = local_claims(ctx)
    claims[f'0x{rva:x}'] = record
    (ctx.private).mkdir(parents=True, exist_ok=True)
    (ctx.private / 'claims.json').write_text(json.dumps(claims, indent=2, sort_keys=True) + '\n')


# ------------------------------------------------------------------ unit skeleton and task

def skeleton(fn, cls, method, area, drafted_by, recipe):
    """(.h text, .cpp text) of a new unit that compiles and passes the lint, with labels filled in."""
    target = fn['build_id']
    label, licence = community_label(fn.get('name_source'))
    label = label or 'GUESS(low)'
    gpl = licence and 'GPL' in licence
    lic_line = (['// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).'] if gpl else [])
    is_dtor = method.startswith('~')
    decl = f'virtual {method}();' if is_dtor else f'void {method}();'
    h = '\n'.join([
        f'// Type declarations for the {cls} translation unit (build {target}).',
        '//',
        '// Labels: v2',
        '// Source exposure: binary-analysis (a local listing of the contributor\'s own copy of the pinned image).',
        *lic_line,
        '// Community names are unverified. Only the members the compared code needs are declared.',
        f'// {cls}: {label}',
        f'// {method}: {label}',
        '#pragma once',
        '',
        f'class {cls} {{',
        'public:',
        f'    // Placeholder signature: replace the return and parameter types with the real ones.',
        f'    {decl}',
        '};',
        ''])
    cpp = '\n'.join([
        f'// {cls}::{method}, build {target}, RVA 0x{fn["rva"]:x}, {fn["size"]} bytes.',
        '//',
        '// Labels: v2',
        f'// Evidence: {fn["evidence"]}.',
        f'// Source exposure: binary-analysis. Drafted by {drafted_by}.',
        *lic_line,
        '// A byte match shows that this source and recipe produce the checked code; it does not verify the',
        '// community name or that the original source looked like this.',
        f'// Recipe: {recipe} (compile this file alone).',
        f'// Only {method} is compared.',
        f'#include "{cls}.h"',
        '',
        f'{cls}::{method}()' if is_dtor else f'void {cls}::{method}()',
        '{',
        '}',
        ''])
    return h, cpp


def contrib_profile(ctx, given=None):
    """The profile for this contributor: the flag, else the remembered one, else the default."""
    name = given or load_config(ctx).get('profile') or profiles.DEFAULT
    if name not in CONTRIB_PROFILES:
        raise Stop(USAGE, f'--profile must be one of {", ".join(CONTRIB_PROFILES)}, not {name!r}')
    return profiles.get(name)


def task_id_for(cls, practice=False):
    # A practice run of an accepted unit gets its own directory, so it never mixes its runs or
    # functions into a real task on the same class and is never picked as "the" task to submit.
    return ('practice-' if practice else 'contrib-') + re.sub(r'[^a-z0-9]+', '-', cls.lower()).strip('-')


def task_dir(ctx, tid):
    return ctx.private / 'tasks' / tid


def load_task(ctx, ident=None):
    """The contributor task named by id, RVA or unit; the only one when none is named."""
    base = ctx.private / 'tasks'
    tasks = sorted(p for p in base.glob('*/task.json')) if base.is_dir() else []
    loaded = [(p.parent, json.loads(p.read_text())) for p in tasks]
    if ident:
        try:
            rva = parse_rva(ident) if re.fullmatch(r'(0x)?[0-9a-fA-F]+', ident) else None
        except Stop:
            rva = None
        pick = [(d, t) for d, t in loaded if d.name == ident or ident in (t['compiled'],)
                or (rva is not None and any(parse_rva(f['rva']) == rva for f in t['functions']))]
    else:
        real = [(d, t) for d, t in loaded if not t.get('contrib', {}).get('practice')]
        pick = real or loaded
    if not pick:
        raise Stop(USAGE, 'no contributor task' + (f' for {ident}' if ident else ''), f'{ctx.cli} start 0x<rva>')
    if len(pick) > 1:
        raise Stop(USAGE, 'several tasks: name one (' + ', '.join(d.name for d, _ in pick) + ')')
    return pick[0]


def refresh_symbols(ctx, tdir, build_id):
    """symbols.json = the public map plus the entries bind added for this task earlier."""
    public = json.loads((ctx.repo / 'reports' / build_id / 'symbol-map.json').read_text())
    path = tdir / 'symbols.json'
    try:
        private = json.loads(path.read_text())
    except (OSError, ValueError):
        private = {}
    extra = {k: v for k, v in (private.get('symbols') or {}).items() if k not in public['symbols']}
    merged = dict(public)
    merged['symbols'] = dict(public['symbols'], **extra)
    path.write_text(json.dumps(merged, indent=2) + '\n')
    return extra


# ------------------------------------------------------------------ commands

def cmd_doctor(ctx, args):
    target = target_manifest(ctx.repo)
    checks, nxt = [], None

    def add(name, ok, detail, fix=None, required=True):
        nonlocal nxt
        checks.append({'check': name, 'ok': ok, 'required': required, 'detail': detail, 'fix': fix})
        mark = 'ok  ' if ok else ('MISS' if required else 'opt ')
        ctx.say(f'{mark} {name}: {detail}')
        if not ok and required and nxt is None:
            nxt = fix
    add('python', sys.version_info >= (3, 11), sys.version.split()[0], 'install Python 3.11 or newer')
    add('git', bool(ctx.which('git')), ctx.which('git') or 'not found', 'install git')
    info, how = resolve_exe(ctx, target, getattr(args, 'exe', None))
    if info is None:
        add('game executable', False, 'SkyrimSE.exe not found in a Steam library',
            f'{ctx.cli} setup --exe "<path to SkyrimSE.exe>"')
    elif info['status'] != 'ok':
        add('game executable', False, wrong_build_message(info, target) if info['status'] == 'wrong-build'
            else f'{info["path"]} does not exist', f'{ctx.cli} setup --exe "<path to SkyrimSE.exe>"')
    else:
        add('game executable', True, f'{info["path"]} ({how}) is {target["version"]}, hash pinned')
    tool = check_toolchain(ctx)
    if not ctx.windows:
        if ctx.platform == 'darwin':
            # Only this project's unpacked Wine counts on macOS: a cask install in /Applications
            # carries a quarantine flag and blocks on a Gatekeeper dialog when run headless.
            wine = str(Path(ctx.env.get('SR_WINE_BIN') or private_wine_bin(ctx)) / 'wine') if mac_wine_ready(ctx) else None
        else:
            wine = ctx.which('wine64') or ctx.which('wine')
        add('wine', bool(wine), wine or 'not found', f'{ctx.cli} setup --yes', required=tool['status'] != 'override')
    detail = {'ok': f'cl 19.16.27054 at {tool.get("bin")} matches tools/verifier/pinned.sha256',
              'override': 'SR_CONTRIB_COMPILER stand-in (not the pinned compiler; results cannot be submitted)',
              'missing': f'no MSVC toolchain under {tool.get("root")}',
              'mismatch': f'toolchain at {tool.get("root")} differs from pinned.sha256 ({", ".join(tool.get("differing", []))})',
              'no-wrapper': 'toolset unpacked but the msvc-wine wrapper is missing'}[tool['status']]
    add('compiler', tool['status'] in ('ok', 'override'), detail,
        f'{ctx.cli} setup --accept-microsoft-license   (a person must accept Microsoft\'s licence first)')
    objdump = find_objdump(ctx)
    add('llvm-objdump (readable listing)', bool(objdump), objdump or 'not found; byte listing only',
        f'{ctx.cli} setup --yes', required=False)
    gh = ctx.which('gh')
    add('gh (GitHub CLI)', bool(gh), gh or 'not found; claims and PRs open as browser links', None, required=False)
    missing_src = [r for r, (p, _rev, _l) in COMMUNITY_SOURCES.items() if not (ctx.repo / p).is_dir()]
    add('community sources (label checks)', not missing_src,
        'present' if not missing_src else 'missing: ' + ', '.join(missing_src), f'{ctx.cli} setup --yes', required=False)
    index = sibling_analysis_dir(ctx) / 'fnv_index.jsonl'
    add('sibling source (FNV decompilation, optional)', index.is_file(),
        f'index at {index}' if index.is_file() else 'not fetched; packs carry no sibling pointers',
        f'{ctx.cli} setup --yes', required=False)
    ok = all(c['ok'] for c in checks if c['required'])
    if ok and nxt is None:
        tasks = list((ctx.private / 'tasks').glob('contrib-*/task.json')) if (ctx.private / 'tasks').is_dir() else []
        nxt = f'{ctx.cli} compare' if tasks else f'{ctx.cli} go'
    return (OK if ok else MISSING), {'checks': checks, 'platform': ctx.platform}, nxt


def package_manager(ctx):
    if ctx.windows:
        for pm in ('winget', 'choco'):
            if ctx.which(pm):
                return pm
        return None
    for pm in ('brew', 'apt-get', 'dnf', 'pacman', 'zypper'):
        if ctx.which(pm):
            return pm
    return None


# Package names per manager. Wine is needed off Windows (the compiler is a Windows program);
# msitools unpacks the Windows SDK there. LLVM gives llvm-objdump (readable listing, side-by-side)
# and llvm-undname (binding by name). SteamCMD is Valve's own client, for the macOS and Linux route.
PACKAGES = {
    'brew': {'wine': ['--cask', 'wine-stable'], 'msitools': ['msitools'], 'llvm': ['llvm'], 'gh': ['gh'],
             'steamcmd': ['--cask', 'steamcmd']},
    'apt-get': {'wine': ['wine', 'wine64', 'winbind'], 'msitools': ['msitools'], 'llvm': ['llvm'], 'gh': ['gh'],
                'steamcmd': ['steamcmd']},
    'dnf': {'wine': ['wine'], 'msitools': ['msitools'], 'llvm': ['llvm'], 'gh': ['gh'], 'steamcmd': ['steamcmd']},
    'pacman': {'wine': ['wine'], 'msitools': ['msitools'], 'llvm': ['llvm'], 'gh': ['github-cli'],
               'steamcmd': None},
    'zypper': {'wine': ['wine'], 'msitools': ['msitools'], 'llvm': ['llvm'], 'gh': ['gh'], 'steamcmd': None},
    'winget': {'llvm': ['LLVM.LLVM'], 'gh': ['GitHub.cli'], 'git': ['Git.Git']},
    'choco': {'llvm': ['llvm'], 'gh': ['gh'], 'git': ['git']},
}


def install_command(ctx, pm, names, accept_sources=False):
    if pm == 'brew':
        casks = [n for n in names if n[:1] == ['--cask']]
        out = []
        plain = [p for n in names if n[:1] != ['--cask'] for p in n]
        if plain:
            out.append(['brew', 'install', *plain])
        out += [['brew', 'install', *n] for n in casks]
        return out
    flat = [p for n in names for p in n]
    sudo = [] if (hasattr(os, 'geteuid') and os.geteuid() == 0) else (['sudo'] if ctx.interactive else ['sudo', '-n'])
    if pm == 'apt-get':
        return [sudo + ['apt-get', 'update', '-q'], sudo + ['apt-get', 'install', '-y', '-q', *flat]]
    if pm == 'dnf':
        return [sudo + ['dnf', 'install', '-y', *flat]]
    if pm == 'pacman':
        return [sudo + ['pacman', '-S', '--needed', '--noconfirm', *flat]]
    if pm == 'zypper':
        return [sudo + ['zypper', '--non-interactive', 'install', *flat]]
    if pm == 'winget':
        # The source agreements are terms of Microsoft's package sources, so they ride on their own
        # flag, never on --yes; without it winget asks on its first run (or fails without a terminal).
        agree = ['--accept-source-agreements'] if accept_sources else []
        return [['winget', 'install', '-e', '--silent', '--source', 'winget', *agree, '--id', p] for p in flat]
    if pm == 'choco':
        return [['choco', 'install', '-y', *flat]]
    return []


def private_wine_bin(ctx):
    return ctx.private / 'wine' / MAC_WINE['app'] / 'Contents' / 'Resources' / 'wine' / 'bin'


def apply_wine_env(ctx):
    """Put this project's Wine first on PATH (macOS) and keep its prefix under .local/, so the
    contributor's own ~/.wine is never touched."""
    if ctx.windows:
        return
    if ctx.platform == 'darwin':
        b = Path(ctx.env.get('SR_WINE_BIN') or private_wine_bin(ctx))
        path = ctx.env.get('PATH', '')
        if (b / 'wine').is_file() and not path.startswith(str(b)):
            ctx.env['PATH'] = f'{b}{os.pathsep}{path}'
    ctx.env.setdefault('WINEPREFIX', str(ctx.private / 'wineprefix'))
    ctx.env.setdefault('WINEDEBUG', '-all')


def mac_wine_ready(ctx):
    b = Path(ctx.env.get('SR_WINE_BIN') or private_wine_bin(ctx))
    return (b / 'wine').is_file()


def install_mac_wine(ctx):
    """WineHQ's macOS build (packaged by Gcenx, the source of the former Homebrew cask), pinned by
    SHA-256 and unpacked under .local/. Downloaded by this tool rather than by a browser or a cask,
    so it carries no quarantine flag and Gatekeeper never asks; nothing goes to /Applications."""
    import tarfile
    dest = ctx.private / 'wine'
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / 'wine.tar.xz'
    if not archive.is_file() or sha256_file(archive) != MAC_WINE['sha256']:
        ctx.say(f'downloading Wine {MAC_WINE["version"]} for macOS (about 185 MB)')
        try:
            with urllib.request.urlopen(MAC_WINE['url'], timeout=900) as resp, open(archive, 'wb') as out:
                shutil.copyfileobj(resp, out)
        except (urllib.error.URLError, OSError) as exc:
            raise Stop(NETWORK, f'cannot download Wine: {exc}', f'{ctx.cli} setup --yes (when online)')
        if sha256_file(archive) != MAC_WINE['sha256']:
            archive.unlink()
            raise Stop(FAILED, 'the Wine download does not match its pinned SHA-256')
    with tarfile.open(archive) as tar:
        try:
            tar.extractall(dest, filter='data')
        except TypeError:  # Python without extraction filters
            # Unfiltered extraction trusts member paths; that is safe here only because the
            # archive was checked against its pinned SHA-256 above.
            tar.extractall(dest)
    archive.unlink()
    apply_wine_env(ctx)
    save_config(ctx, wine=str(private_wine_bin(ctx)))


def wanted_packages(ctx, tool):
    want = []
    if not ctx.windows and tool['status'] != 'override':
        if ctx.platform != 'darwin' and not (ctx.which('wine64') or ctx.which('wine')):
            want.append('wine')
        if not ctx.which('msiextract') and tool['status'] != 'ok':
            want.append('msitools')
    if not find_objdump(ctx):
        want.append('llvm')
    if ctx.windows and not ctx.which('git'):
        want.append('git')
    return want


def fetch_sources(ctx, sources=None):
    """Shallow clones of the pinned community naming sources, for the label and origin checks."""
    done = []
    for repo, (rel, rev, _lic) in (COMMUNITY_SOURCES if sources is None else sources).items():
        dest = ctx.repo / rel
        if (dest / '.git').is_dir():
            head = git(ctx, 'rev-parse', 'HEAD', check=False, cwd=dest)
            if head == rev:
                continue
        dest.mkdir(parents=True, exist_ok=True)
        for args in (['init', '-q'], ['fetch', '-q', '--depth', '1', f'https://github.com/{repo}.git', rev],
                     ['-c', 'advice.detachedHead=false', 'checkout', '-q', 'FETCH_HEAD']):
            proc = ctx.run(['git', *args], cwd=dest, capture_output=True, text=True)
            if proc.returncode != 0:
                raise Stop(NETWORK, f'cannot fetch {repo}@{rev[:7]}: {proc.stderr.strip()[:200]}',
                           f'{ctx.cli} setup --yes   (retry when online)')
        done.append(repo)
    return done


def sibling_analysis_dir(ctx):
    return ctx.private / 'analysis'


def build_sibling_index(ctx):
    """The private FNV lookup index (tools/build_fnv_index.py) joined by name to the public
    inventory, since a contributor has no Ghidra tables: `start` then lists the same-named FNV
    method and the class's small methods. Returns the number of our functions joined, or None."""
    repo, rel, _rev = SIBLING_SOURCE
    clone = ctx.repo / rel
    if not (clone / 'build/units.json').is_file():
        return None
    out = sibling_analysis_dir(ctx)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / 'functions.jsonl', 'w') as fh:
        for fn in inventory(ctx.repo)['functions']:
            if PLAIN_NAME.fullmatch(fn.get('name') or ''):
                fh.write(json.dumps({'rva': fn['rva'], 'names': [{'name': fn['name'], 'how': 'community',
                                                                    'source': 'data/progress.json'}]}) + '\n')
    proc = ctx.run([sys.executable, str(ctx.repo / 'tools/build_fnv_index.py'), '--fnv', str(clone),
                    '--analysis', str(out)], cwd=ctx.repo, capture_output=True, text=True)
    if proc.returncode != 0:
        raise Stop(FAILED, f'building the {repo} index failed: {(proc.stderr or proc.stdout).strip()[-200:]}')
    m = re.search(r'our functions joined by name: (\d+)', proc.stdout)
    return int(m.group(1)) if m else 0


def sibling_section(ctx, cls, rvas):
    """Lines of the "Sibling source" section for a task, [] without the index or a match."""
    try:
        from export_pack import sibling_lines
    except Exception:  # noqa: BLE001 - the section is optional help, never required
        return []
    return sibling_lines(cls, rvas, root=sibling_analysis_dir(ctx))


def licence_url(vsman):
    """The Build Tools licence link from the pinned installer manifest, if it names one."""
    try:
        data = json.loads(Path(vsman).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return None
    for pkg in data.get('packages', []):
        if pkg.get('id') == 'Microsoft.VisualStudio.Product.BuildTools':
            for res in pkg.get('localizedResources') or []:
                if str(res.get('language', '')).lower() == 'en-us' and res.get('license'):
                    return res['license']
    return None


def install_toolchain(ctx, accept):
    """The verifier recipe (see tools/verifier/recipe_pins.py) on this machine: msvc-wine at its
    pinned commit, the pinned VS 2017 15.9 manifest, toolset and SDK from Microsoft's servers, then
    the binaries checked against pinned.sha256. Resumable: finished steps are skipped."""
    pins = recipe_constants(ctx.repo)
    work = ctx.private / 'toolchain-work'
    work.mkdir(parents=True, exist_ok=True)
    src = work / 'msvc-wine'
    at_pin = (src / '.git').is_dir() and git(ctx, 'rev-parse', 'HEAD', check=False, cwd=src) == pins['MSVC_WINE_COMMIT']
    if not at_pin:
        if not (src / '.git').is_dir():
            proc = ctx.run(['git', 'clone', '-q', pins['MSVC_WINE_URL'], str(src)], capture_output=True, text=True)
            if proc.returncode != 0:
                raise Stop(NETWORK, f'cannot clone msvc-wine: {proc.stderr.strip()[:200]}', f'{ctx.cli} setup (when online)')
        git(ctx, '-c', 'advice.detachedHead=false', 'checkout', '-q', pins['MSVC_WINE_COMMIT'], cwd=src)
    vsman = work / 'VisualStudio.vsman'
    if not vsman.is_file() or sha256_file(vsman) != pins['VSMAN_SHA256']:
        ctx.say('downloading the pinned Visual Studio 2017 15.9 installer manifest from Microsoft')
        try:
            with urllib.request.urlopen(pins['VSMAN_URL'], timeout=120) as resp:
                vsman.write_bytes(resp.read())
        except (urllib.error.URLError, OSError) as exc:
            raise Stop(NETWORK, f'cannot download the installer manifest: {exc}', f'{ctx.cli} setup (when online)')
        if sha256_file(vsman) != pins['VSMAN_SHA256']:
            vsman.unlink()
            raise Stop(FAILED, 'the installer manifest does not match its pinned SHA-256; the recipe stops here '
                       '(tools/verifier/README.md, "Known limits of the recipe")')
    url = licence_url(vsman)
    if not url:
        # Acceptance needs a licence a person can read; without a concrete link nothing is accepted.
        raise Stop(FAILED, 'the pinned installer manifest names no licence link, so no licence can be shown '
                   'for acceptance; nothing was installed', 'report this in an issue (tools/verifier/README.md)')
    if accept:
        ctx.say(f'Microsoft Build Tools for Visual Studio 2017 licence, accepted by the person who passed '
                f'--accept-microsoft-license: {url}')
    else:
        ctx.say(f'Microsoft Build Tools for Visual Studio 2017 licence: {url}')
        if not ctx.interactive:
            raise Stop(CONSENT, f'installing the compiler accepts Microsoft\'s licence ({url})',
                       f'{ctx.cli} setup --accept-microsoft-license   (only after a person has read and accepted it)',
                       licence=url)
        if input('Do you accept this licence? Type "yes": ').strip().lower() != 'yes':
            raise Stop(CONSENT, 'licence not accepted; no compiler installed')
    dest = toolchain_root(ctx)
    common = [sys.executable, '-I', str(src / 'vsdownload.py'), '--manifest', str(vsman), '--major', '15',
              '--host-arch', 'x64', '--architecture', 'x64', '--with-default', 'no', '--with-msvc', 'yes',
              '--with-sdk', 'yes', '--sdk-version', pins['SDK_VERSION'], '--accept-license']
    # A persistent download cache: without one vsdownload.py discards every finished payload when
    # one fails, so an interrupted 0.75 GB download on a slow link would start over. vsdownload.py
    # checks each cached payload against the manifest's SHA-256 before reusing it.
    cache = work / 'cache'
    if not toolchain_bins(dest):
        ctx.say(f'downloading and unpacking the toolset and SDK into {dest} (about 0.75 GB from Microsoft, '
                f'about 3.5 GB of disk); an interrupted download resumes from {cache} on the next run')
        proc = ctx.run(common + ['--cache', str(cache), '--dest', str(dest)], cwd=work)
        if proc.returncode != 0:
            raise Stop(FAILED, 'vsdownload.py failed (see its output above); finished downloads are kept',
                       f'{ctx.cli} setup --accept-microsoft-license   (resumes)')
    shutil.rmtree(cache, ignore_errors=True)
    if not ctx.windows and not (dest / 'bin/x64/cl').is_file():
        proc = ctx.run(['bash', str(src / 'install.sh'), str(dest)], cwd=work)
        if proc.returncode != 0:
            raise Stop(FAILED, 'msvc-wine install.sh failed (see its output above)', f'{ctx.cli} doctor')
    save_config(ctx, msvc=str(dest), microsoft_licence_accepted=True)
    return check_toolchain(ctx)


def cmd_setup(ctx, args):
    target = target_manifest(ctx.repo)
    steps = []

    def step(name, status, detail):
        steps.append({'step': name, 'status': status, 'detail': detail})
        ctx.say(f'[{status}] {name}: {detail}')
    if sys.version_info < (3, 11):
        raise Stop(MISSING, 'Python 3.11 or newer is needed', 'install a newer Python and rerun')
    if not ctx.which('git'):
        raise Stop(MISSING, 'git is needed', 'install git and rerun')
    # 1. Packages first, so SteamCMD is available for the executable step.
    tool = check_toolchain(ctx)
    want = wanted_packages(ctx, tool)
    pm = package_manager(ctx)
    if getattr(args, 'steamcmd', False) and not ctx.which('steamcmd'):
        if pm == 'apt-get':
            # Debian's package shows Valve's Steam licence in a debconf dialog; a person answers it,
            # so this tool never installs it with -y or preseeds the answer.
            step('steamcmd', 'needs-person', 'run: sudo apt install steamcmd   (it shows the Steam licence for you '
                 'to accept; Ubuntu needs the multiverse repository and i386: sudo add-apt-repository multiverse; '
                 'sudo dpkg --add-architecture i386; sudo apt update)')
        elif ctx.windows:
            step('steamcmd', 'needs-person', 'download SteamCMD from Valve: '
                 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip (unzip it to C:\\steamcmd)')
        else:
            want.append('steamcmd')
    if want:
        table = PACKAGES.get(pm or '', {})
        names = [table[w] for w in want if table.get(w)]
        cmds = install_command(ctx, pm, names, getattr(args, 'accept_winget_source_agreements', False)) if pm else []
        shown = ' && '.join(' '.join(shlex.quote(c) for c in cmd) for cmd in cmds)
        if not cmds:
            step('packages', 'needs-person', f'install {", ".join(want)} with your package manager')
        elif args.no_install:
            step('packages', 'skipped', f'would run: {shown}')
        elif ctx.ask(f'Install {", ".join(want)} with: {shown}?', '--yes'):
            for cmd in cmds:
                proc = ctx.run(cmd)
                if proc.returncode != 0:
                    if pm == 'winget' and '--accept-source-agreements' not in cmd:
                        raise Stop(CONSENT, f'package install failed: {" ".join(cmd)}; winget may be waiting for '
                                   'you to accept the terms of its package source',
                                   f'run it yourself in a terminal, or after reading the terms: {ctx.cli} setup '
                                   '--yes --accept-winget-source-agreements', steps=steps)
                    raise Stop(MISSING, f'package install failed: {" ".join(cmd)}',
                               f'run it yourself (it may need your password): {shown}', steps=steps)
            step('packages', 'installed', ', '.join(want))
        else:
            step('packages', 'skipped', 'declined')
    else:
        step('packages', 'present', 'nothing to install')
    if not ctx.windows and ctx.platform == 'darwin' and not ctx.env.get('SR_CONTRIB_COMPILER'):
        rosetta = ctx.run(['arch', '-x86_64', '/usr/bin/true'], capture_output=True).returncode == 0 \
            if os.uname().machine == 'arm64' else True
        if not rosetta:
            step('rosetta', 'needs-person', 'Wine on Apple silicon needs Rosetta 2, which has its own Apple licence')
            raise Stop(CONSENT, 'Rosetta 2 is not installed; installing it accepts Apple\'s licence',
                       'a person runs: softwareupdate --install-rosetta   (then rerun setup)', steps=steps)
        if mac_wine_ready(ctx):
            step('wine', 'present', str(Path(ctx.env.get('SR_WINE_BIN') or private_wine_bin(ctx))))
        elif args.no_install:
            step('wine', 'skipped', f'would download {MAC_WINE["url"]}')
        elif ctx.ask(f'Download Wine {MAC_WINE["version"]} (WineHQ build, about 185 MB) into {ctx.private / "wine"}?',
                     '--yes'):
            install_mac_wine(ctx)
            step('wine', 'installed', str(private_wine_bin(ctx)))
        else:
            raise Stop(CONSENT, 'Wine is needed to run the compiler on macOS', f'{ctx.cli} setup --yes', steps=steps)
    # 2. The game executable.
    info, how = resolve_exe(ctx, target, args.exe)
    steamcmd = ctx.which('steamcmd')
    if (info is None or info['status'] != 'ok') and getattr(args, 'steamcmd', False) and steamcmd \
            and ctx.interactive and not args.exe:
        # SteamCMD runs in this terminal: the person types the login, password and guard code into
        # it directly, so none of them pass through this process.
        ctx.say('\n'.join(steamcmd_route(ctx)))
        if ctx.ask('Start SteamCMD now (you type the steps above at its prompt)?', '--steamcmd'):
            (ctx.private / 'game').mkdir(parents=True, exist_ok=True)
            subprocess.run([steamcmd], env=ctx.env)
            info, how = resolve_exe(ctx, target, None)
    if info is not None and info['status'] == 'ok':
        save_config(ctx, exe=info['path'])
        step('game executable', 'ok', f'{info["path"]} ({how}), {target["version"]}, SHA-256 pinned')
    else:
        detail = wrong_build_message(info, target) if info and info['status'] == 'wrong-build' else \
            'SkyrimSE.exe not found' + (f' at {info["path"]}' if info else ' in a Steam library')
        step('game executable', 'needs-person', detail)
        raise Stop(MISSING, detail, f'{ctx.cli} setup --exe "<path to SkyrimSE.exe>"', steps=steps,
                   steamcmd_route=steamcmd_route(ctx), pinned={k: target[k] for k in ('version', 'store', 'image_sha256')})
    # 3. Community sources for the label and origin checks.
    if not args.no_sources:
        try:
            fetched = fetch_sources(ctx)
            step('community sources', 'ok', ('fetched ' + ', '.join(fetched)) if fetched else 'present at their pins')
        except Stop as exc:
            step('community sources', 'skipped', exc.message)
    # 3b. The FNV decompilation (optional): read for shape and names, never evidence.
    if not args.no_sources and not getattr(args, 'no_sibling', False):
        repo, rel, rev = SIBLING_SOURCE
        try:
            fetched = fetch_sources(ctx, {repo: (rel, rev, 'no-licence')})
            joined = build_sibling_index(ctx)
            step('sibling source', 'ok', f'{repo}@{rev[:8]} ' + ('fetched' if fetched else 'present')
                 + f'; index joins {joined} inventory functions by name')
        except Stop as exc:
            step('sibling source', 'skipped', exc.message)
    # 4. The compiler.
    if tool['status'] in ('ok', 'override'):
        step('compiler', tool['status'], tool.get('bin') or 'SR_CONTRIB_COMPILER')
    else:
        tool = install_toolchain(ctx, args.accept_microsoft_license)
        if tool['status'] != 'ok':
            raise Stop(MISSING, f'toolchain after install: {tool["status"]} {tool.get("differing", "")}',
                       f'{ctx.cli} doctor', steps=steps)
        step('compiler', 'installed', tool['bin'])
    # 5. Self-test: a function the project already matched must pass here too.
    if not args.no_self_test:
        try:
            code, data, _n = run_self_test(ctx)
        except Stop as exc:
            step('self-test', 'fail', exc.message)
            raise Stop(exc.code, f'self-test: {exc.message}', exc.next_action or f'{ctx.cli} doctor',
                       steps=steps, **exc.data)
        if data.get('skipped'):
            step('self-test', 'skipped', data['note'])
        else:
            step('self-test', 'pass' if code == OK else 'fail',
                 f'0x{SELF_TEST_RVA:x} compiled and compared: ' + ', '.join(
                     f'{f["rva"]} {f["result"]} {f["reason"]}' for f in data.get('functions', [])))
        if code != OK:
            raise Stop(code, 'self-test failed: the local toolchain does not reproduce an accepted match',
                       f'{ctx.cli} doctor', steps=steps, self_test=data)
    return OK, {'steps': steps}, f'{ctx.cli} next'


def run_self_test(ctx):
    data = inventory(ctx.repo)
    fn = find_function(data, SELF_TEST_RVA)
    if fn is None or fn['status'] != 'matched':
        return OK, {'functions': [], 'skipped': True,
                    'note': f'0x{SELF_TEST_RVA:x} is not a matched function in data/progress.json; nothing proven'}, None
    args = argparse.Namespace(rva=[f'0x{SELF_TEST_RVA:x}'], practice=True, drafted_by='self-test', area=None,
                              no_branch=True, recipe=None, force=False)
    start(ctx, args, quiet=True)
    return run_compare(ctx, task_id_for(PLAIN_NAME.fullmatch(fn['name']).group(1), practice=True))


def cmd_next(ctx, args):
    data = inventory(ctx.repo)
    claimed, online = set(), True
    try:
        index = ctx.github().open_items()
        me = ctx.github().user()
        claimed = {f['rva'] for f in data['functions']
                   if batch_claims.claimed(index, f['rva'], me) and
                   any(it.get('build_id') in (None, f['build_id']) for it in
                       batch_claims.claimed(index, f['rva'], me))}
    except Offline:
        online = False
    claimed |= {parse_rva(k) for k in local_claims(ctx)}
    rows = [c for c in candidates(ctx.repo, data, claimed, args.max_size) if c['startable']][:args.count]
    for c in rows:
        ctx.say(f'{c["rva"]:>10}  {c["size"]:>5} B  {c["name"]}  -> {c["unit"]}' + ('' if not c['unit_exists']
                                                                                   else '  (existing unit)'))
    if not online:
        ctx.say('note: GitHub not reachable; claims by others are not excluded')
    if not rows:
        return OK, {'candidates': [], 'claims_checked': online}, None
    return OK, {'candidates': rows, 'claims_checked': online}, f'{ctx.cli} claim {rows[0]["rva"]}'


def claim_selection(ctx, args, data):
    values = getattr(args, 'rva', []) or []
    values = [values] if isinstance(values, str) else list(values)
    for file in getattr(args, 'lists', []) or []:
        for line in Path(file).read_text().splitlines():
            if line.strip() and not line.lstrip().startswith('#'):
                values.append(line.split()[0])
    addresses = {parse_rva(v) for v in values}
    for cls in getattr(args, 'classes', []) or []:
        selected = [f for f in data['functions'] if (f.get('name') or '').rsplit('::', 1)[0] == cls
                    and f['status'] != 'matched']
        if not selected:
            raise Stop(USAGE, f'class {cls} has no unmatched functions')
        addresses.update(f['rva'] for f in selected)
    ranges = []
    for value in getattr(args, 'ranges', []) or []:
        try:
            start, end = map(parse_rva, value.split('-', 1))
        except (ValueError, Stop):
            raise Stop(USAGE, 'range must be 0x<start>-0x<end>') from None
        if end <= start:
            raise Stop(USAGE, 'range end must be greater than start')
        ranges.append((start, end))
        addresses.update(f['rva'] for f in data['functions'] if start <= f['rva'] < end and f['status'] != 'matched')
    if not addresses:
        raise Stop(USAGE, 'select RVAs, --class, --list or --range')
    merged = []
    for a, b in sorted(ranges):
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    ranges = merged
    functions = []
    for address in sorted(addresses):
        fn = find_function(data, address)
        if fn is None:
            raise Stop(USAGE, f'0x{address:x} is not in data/progress.json')
        if fn['status'] == 'matched':
            raise Stop(USAGE, f'0x{address:x} is already matched', f'{ctx.cli} next')
        functions.append(fn)
    entries = ranges + [(r, r + 1) for r in sorted(addresses) if not any(a <= r < b for a, b in ranges)]
    return functions, entries


def cmd_claim(ctx, args):
    data = inventory(ctx.repo)
    functions, entries = claim_selection(ctx, args, data)
    build = functions[0]['build_id']
    addresses = [f['rva'] for f in functions]
    first = addresses[0]
    gh = ctx.github()
    try:
        index = gh.open_items()
    except Offline as exc:
        if not args.offline_ok:
            raise Stop(NETWORK, f'cannot reach GitHub to check claims ({exc})',
                       f'{ctx.cli} claim 0x{first:x} when online, or --offline-ok to start unclaimed')
        for address in addresses:
            save_local_claim(ctx, address, {'status': 'unpublished', 'url': None})
        ctx.say('WARNING: claim recorded locally only; others cannot see it. Run claim again when online.')
        return OK, {'rva': f'0x{first:x}', 'claim': 'unpublished'}, f'{ctx.cli} start 0x{first:x}'
    if getattr(args, 'github_user', None):
        save_config(ctx, github_user=args.github_user)
    me = gh.user()
    def overlapping(idx):
        if isinstance(idx, batch_claims.ClaimIndex):
            return [it for it in batch_claims.ClaimIndex(idx.records, build).overlaps(entries, active=False)]
        result = []
        for address in addresses:
            for it in idx.get(address, []):
                if it not in result:
                    result.append(it)
        return result
    items = overlapping(index)
    if not me and items:
        raise Stop(USAGE, 'GitHub login is unknown; cannot tell whether an existing claim is yours',
                   f'{ctx.cli} claim 0x{first:x} --github-user <your-login>', claims=items)
    mine, fresh, stale = claim_state(items, me)
    if fresh:
        raise Stop(CLAIMED, 'scope is claimed: ' + ', '.join(f'#{i["number"]} {i["url"]} by {i["author"]}' for i in fresh),
                   f'{ctx.cli} next', claims=fresh)
    if stale and not args.take_over:
        raise Stop(CLAIMED, f'lapsed claim #{stale[0]["number"]}; use --take-over',
                   f'{ctx.cli} claim 0x{first:x} --take-over', claims=stale)
    ranges_covered = all(any(a <= start and end <= b for it in mine for a, b in it.get('entries', []))
                         for start, end in entries if end > start + 1)
    if mine and ranges_covered and all(any(it in mine for it in index.get(address, [])) for address in addresses):
        for address in addresses:
            save_local_claim(ctx, address, {'status': 'published', 'url': mine[0]['url']})
        ctx.say(f'already yours: {mine[0]["url"]}')
        return OK, {'rva': f'0x{first:x}', 'claim': mine[0]['url']}, f'{ctx.cli} start 0x{first:x}'
    public = batch_claims.git_json(ctx.repo)
    counts = {e: sum(e[0] <= f['rva'] < e[1] and f['build_id'] == build for f in data['functions']) for e in entries}
    plans = batch_claims.parts(build, entries, public, me or 'claimant', counts=counts)
    urls, links = [], []
    for title, text, chunk in plans:
        url = gh.create_issue(title, text)
        if not url:
            links.append(gh.new_issue_link(title, text))
            continue
        urls.append(url)
        try:
            after = overlapping(gh.open_items(refresh=True))
        except Offline:
            after = []
        rivals = [i for i in claim_state(after, me)[1] if i['url'] != url and int(i['number']) < issue_number(url)]
        if rivals:
            for created in urls:
                gh.close(issue_number(created), f'Withdrawn: {rivals[0]["url"]} claimed the overlapping scope first.')
            saved = local_claims(ctx)
            saved = {key: value for key, value in saved.items() if value.get('url') not in urls}
            ctx.private.mkdir(parents=True, exist_ok=True)
            (ctx.private / 'claims.json').write_text(json.dumps(saved) + '\n')
            raise Stop(CLAIMED, f'older claim #{rivals[0]["number"]} won; your claim was withdrawn', claims=rivals)
        for address in addresses:
            if any(a <= address < b for a, b in chunk):
                save_local_claim(ctx, address, {'status': 'published', 'url': url})
        ctx.say(f'claimed: {url}')
    if links:
        ctx.say('gh is not signed in; file these issues, then run claim again:')
        for link in links:
            ctx.say(link)
        return OK, {'rva': f'0x{first:x}', 'claim': 'link-only', 'link': links[0], 'links': links}, 'file the issues and run claim again'
    for it in stale:
        for offset in range(0, len(entries), 500):
            markers = '\n'.join(f'<!-- skyrim-claim-takeover-v1 0x{a:x}-0x{b:x} -->'
                                for a, b in entries[offset:offset + 500])
            gh.comment(it['number'], f'Taking over overlapping functions after 24 hours without activity. '
                       f'New claim: #{issue_number(urls[0])}.\n' + markers)
    return OK, {'rva': f'0x{first:x}', 'claim': urls[0], 'claims': urls}, f'{ctx.cli} start 0x{first:x}'


def cmd_release(ctx, args):
    rva = parse_rva(args.rva)
    gh = ctx.github()
    reason = args.reason or 'giving the function back'
    closed = []
    try:
        me = gh.user()
        for it in gh.open_items().get(rva, []):
            if len(it.get('entries', [])) > 1 or any(b > a + 1 for a, b in it.get('entries', [])):
                ctx.say(f'batch #{it["number"]}: edit its scope on GitHub or close the whole issue to release it')
                continue
            if it['author'] == me and not it['pull_request'] and gh.close(it['number'], f'Released: {reason}'):
                closed.append(it['url'])
    except Offline:
        pass
    claims = local_claims(ctx)
    claims.pop(f'0x{rva:x}', None)
    if (ctx.private / 'claims.json').exists():
        (ctx.private / 'claims.json').write_text(json.dumps(claims, indent=2) + '\n')
    ctx.say('released' + (': ' + ', '.join(closed) if closed else ' locally (close the claim issue on GitHub if any)'))
    return OK, {'rva': f'0x{rva:x}', 'closed': closed}, f'{ctx.cli} next'


def write_source(path, text):
    """A unit file with LF line ends on every platform: the source digest hashes the bytes on disk,
    and text mode on Windows would write CRLF and change the digest."""
    Path(path).write_text(text, encoding='utf-8', newline='\n')


def start(ctx, args, quiet=False):
    data = inventory(ctx.repo)
    target = target_manifest(ctx.repo)
    fns = []
    for text in args.rva:
        fn = find_function(data, parse_rva(text))
        if fn is None:
            raise Stop(USAGE, f'{text} is not in data/progress.json', f'{ctx.cli} next')
        if fn['status'] == 'matched' and not args.practice:
            raise Stop(USAGE, f'{text} is already matched; use --practice to try it as an exercise', f'{ctx.cli} next')
        fns.append(fn)
    m = [PLAIN_NAME.fullmatch(fn.get('name') or '') for fn in fns]
    if not all(m):
        raise Stop(USAGE, 'only plain Class::Method names can be started with a skeleton', f'{ctx.cli} next')
    classes = {x.group(1) for x in m}
    if len(classes) != 1:
        raise Stop(USAGE, 'one unit per task: give functions of one class')
    cls = classes.pop()
    if args.area is not None and not re.fullmatch(r'[a-z][a-z0-9_]*', args.area):
        raise Stop(USAGE, f'--area must be one lower-case directory name under reconstruction/ ([a-z][a-z0-9_]*), '
                   f'not {args.area!r}')
    area, header, cpp = unit_files(ctx.repo, cls, args.area)
    if area is None:
        raise Stop(USAGE, f'no area rule for class {cls} (reconstruction/README.md, "Layout")',
                   f'{ctx.cli} start {" ".join(args.rva)} --area <area>  (ask in your claim issue which area)')
    exe = require_exe(ctx, target)['path']
    tdir = task_dir(ctx, task_id_for(cls, args.practice))
    tdir.mkdir(parents=True, exist_ok=True)
    names = public_names(ctx.repo, data)
    smap = json.loads((ctx.repo / 'reports' / target['build_id'] / 'symbol-map.json').read_text())['symbols']
    by_rva = {e['rva']: n for n, e in smap.items() if isinstance(e, dict) and isinstance(e.get('rva'), int)}
    try:
        old = json.loads((tdir / 'task.json').read_text())
    except (OSError, ValueError):
        old = {}
    functions = {parse_rva(f['rva']): f for f in old.get('functions', [])}
    for fn, mm in zip(fns, m):
        dest, _pack = write_pack(ctx, exe, fn, names)
        functions.setdefault(fn['rva'], {
            'rva': f'0x{fn["rva"]:x}', 'size': fn['size'],
            'symbol': by_rva.get(fn['rva']) or f'unbound:{fn["name"]}',
            'function_id': fn['id'], 'community_name': fn['name'], 'pack': str(dest)})
    recipe = args.recipe or old.get('recipe') or DEFAULT_RECIPE
    sibling = sibling_section(ctx, cls, sorted(functions))
    if sibling:
        (tdir / 'sibling.md').write_text(f'# {cls}: pointers into the FNV decompilation (private)\n'
                                         + '\n'.join(sibling) + '\n')
    created = []
    if not (ctx.repo / cpp).exists():
        if args.practice:
            raise Stop(USAGE, f'{cpp} does not exist; practice works on accepted units only')
        drafted = args.drafted_by or load_config(ctx).get('drafted_by')
        if not drafted:
            raise Stop(CONSENT, 'say who drafts the unit (a person, and the AI model if one writes code)',
                       f'{ctx.cli} start {" ".join(args.rva)} --drafted-by "<your name>, assisted by <model or none>"')
        h_text, cpp_text = skeleton(fns[0], cls, m[0].group(2), area, drafted, recipe)
        if not (ctx.repo / header).exists():
            (ctx.repo / header).parent.mkdir(parents=True, exist_ok=True)
            write_source(ctx.repo / header, h_text)
            created.append(header)
        write_source(ctx.repo / cpp, cpp_text)
        created.append(cpp)
        save_config(ctx, drafted_by=drafted)
    elif not args.practice:
        ctx.say(f'{cpp} exists: add each new function and its "RVA 0x<rva>, <n> bytes" header line yourself. '
                'Editing an accepted unit makes its accepted functions stale until the project re-confirms them.')
    prof = contrib_profile(ctx, getattr(args, 'profile', None))
    save_config(ctx, profile=prof['name'])
    task = {'task_id': tdir.name, 'build_id': target['build_id'], 'compiled': cpp, 'recipe': recipe,
            'symbols': 'symbols.json', 'functions': sorted(functions.values(), key=lambda f: parse_rva(f['rva'])),
            'contrib': {'practice': bool(args.practice), 'unit': [header, cpp], 'profile': prof['name']}}
    (tdir / 'task.json').write_text(json.dumps(task, indent=2) + '\n')
    refresh_symbols(ctx, tdir, target['build_id'])
    branch = None
    if not args.no_branch and not args.practice:
        branch = f'contrib/{tdir.name[len("contrib-"):]}'
        exists = ctx.run(['git', 'rev-parse', '--verify', '--quiet', branch], cwd=ctx.repo,
                         capture_output=True).returncode == 0
        git(ctx, 'switch', *([] if exists else ['-c']), branch)
    packs = [f['pack'] for f in task['functions']]
    if not quiet:
        for p in packs:
            ctx.say(f'pack (private, read it locally, never paste it anywhere): {p}/bytes.txt'
                    + (' and listing.txt' if (Path(p) / 'listing.txt').is_file() else ''))
        if sibling:
            ctx.say(f'sibling source pointers (FNV; shape and names only, never evidence): {tdir / "sibling.md"}')
        ctx.say(f'unit: {header} and {cpp}' + (' (skeleton created)' if created else ''))
        ctx.say(f'profile {prof["name"]}: read {"; ".join(prof["contrib_docs"])}; stop after '
                f'{prof["contrib_max_tries"]} compare runs without a pass. {prof["cost"]}')
    return OK, {'task': tdir.name, 'unit': [header, cpp], 'created': created, 'packs': packs, 'branch': branch,
                'practice': bool(args.practice), 'sibling': str(tdir / 'sibling.md') if sibling else None,
                'profile': prof['name'], 'read': prof['contrib_docs'], 'max_tries': prof['contrib_max_tries'],
                'cost': prof['cost']}, \
        f'edit {cpp}, then {ctx.cli} compare'


def cmd_start(ctx, args):
    return start(ctx, args)


def candidate_size(obj_path, symbol):
    from bind import defined_functions
    from pecoff import CoffObject
    try:
        obj = CoffObject(Path(obj_path).read_bytes())
        sec = defined_functions(obj).get(symbol)
        return obj.section(sec).raw_size if sec else None
    except Exception:  # noqa: BLE001 - a size for display only
        return None


def run_compare(ctx, ident=None, root=None):
    """Compile the task's unit and compare each function; returns (code, data, next)."""
    import bind
    import verify_function
    root = Path(root or ctx.repo)
    tdir, task = load_task(ctx, ident)
    target = target_manifest(root)
    exe = require_exe(ctx, target)['path']
    tool = check_toolchain(ctx)
    runs = tdir / 'runs'
    number = len([p for p in runs.glob('[0-9][0-9][0-9]')]) + 1 if runs.is_dir() else 1
    out = runs / f'{number:03d}'
    refresh_symbols(ctx, tdir, task['build_id'])
    built = compile_unit(ctx, root, task['compiled'], task['recipe'], out, tool)
    objdump = find_objdump(ctx)
    bound = bind.bind(tdir, built['object'], exe, objdump, repo=root)
    bind_lines = bind.describe(bound, tdir)
    task = json.loads((tdir / 'task.json').read_text())
    results = []
    for fn in task['functions']:
        rva = parse_rva(fn['rva'])
        fdir = out / f'0x{rva:x}'
        fdir.mkdir(parents=True, exist_ok=True)
        vtask = {'task_id': f'{task["task_id"]}-{rva:x}', 'build_id': task['build_id'],
                 'target_image_sha256': target['image_sha256'], 'rva': rva, 'size': fn['size'],
                 'symbol': fn['symbol'], 'source_revision': built['digest'], 'source_path': task['compiled'],
                 'recipe_sha256': built['recipe_sha256']}
        (fdir / 'task-file.json').write_text(json.dumps({
            'verify_task_schema': 1, 'task': vtask, 'recipe': str(root / task['recipe']),
            'symbols': str(tdir / 'symbols.json'), 'manifest': str(root / 'builds/target.json')}, indent=2))
        diag = verify_function.PRIVATE_ROOT / 'contrib' / 'diagnostics' / f'{task["task_id"]}-{rva:x}.json'
        status, _text = verify_function.run(fdir / 'task-file.json', built['object'], built['build_record'], exe,
                                            fdir / 'report.json', diag)
        report = json.loads((fdir / 'report.json').read_text())
        m = re.search(r'at \+0x([0-9a-f]+)', report.get('detail') or '')
        cov = report.get('coverage') or {}
        results.append({'rva': f'0x{rva:x}', 'name': fn.get('community_name'), 'result': report.get('result'),
                        'reason': report.get('reason'), 'detail': verify_function.mask(str(report.get('detail'))),
                        'hint': verify_function.HINTS.get(report.get('reason') or '', ''),
                        'first_mismatch': f'+0x{m.group(1)}' if m else None,
                        'candidate_size': candidate_size(built['object'], fn['symbol']), 'target_size': fn['size'],
                        'coverage': {k: cov.get(k) for k in ('code_bytes_total', 'code_bytes_exact',
                                                             'code_bytes_by_reference', 'unwind')},
                        'code_section_sha256': (report.get('candidate') or {}).get('code_section_sha256')})
        if objdump:
            import disasm
            disasm.write_side_by_side(fdir / 'side-by-side.txt', objdump, exe, built['object'], fn['symbol'],
                                      rva, fn['size'])
    first = json.loads((out / f'0x{parse_rva(task["functions"][0]["rva"]):x}' / 'report.json').read_text())
    summary = {'task': task['task_id'], 'run': number, 'unit': task['compiled'], 'source_revision': built['digest'],
               'recipe': task['recipe'], 'recipe_sha256': built['recipe_sha256'],
               'compiler': 'pinned' if built['compiler'] in ('wine', 'native') else 'override',
               'image_sha256_pinned': True, 'comparator': first.get('comparator'),
               'contract_version': first.get('contract_version'), 'functions': results,
               'bind': [line.strip() for line in bind_lines], 'practice': task.get('contrib', {}).get('practice', False),
               'private_dir': str(out)}
    (tdir / 'last-compare.json').write_text(json.dumps(summary, indent=2) + '\n')
    passed = sum(r['result'] == 'pass' for r in results)
    ctx.say(f'run {number}: {passed}/{len(results)} pass ({summary["compiler"]} compiler)')
    for r in results:
        size = f'{r["candidate_size"]}/{r["target_size"]} B'
        ctx.say(f'  {r["rva"]} {r["name"]}: {r["result"].upper()} {r["reason"]} {r["first_mismatch"] or ""} {size}')
        if r['result'] != 'pass':
            ctx.say(f'    hint: {r["hint"]}')
    for line in bind_lines:
        ctx.say(line)
    if objdump:
        for r in results:
            ctx.say(f'private side-by-side: {out / r["rva"] / "side-by-side.txt"} (read locally; never paste it anywhere)')
    nxt = f'{ctx.cli} submit' if passed == len(results) else f'revise the source, then {ctx.cli} compare'
    prof = contrib_profile(ctx, task.get('contrib', {}).get('profile'))
    summary['profile'], summary['max_tries'] = prof['name'], prof['contrib_max_tries']
    if passed < len(results) and number >= prof['contrib_max_tries'] and not summary['practice']:
        # Advice only: a contributor may go on, but a weak model rarely recovers past this point.
        first_rva = task['functions'][0]['rva']
        nxt = (f'stop: {number} compare runs under profile {prof["name"]} without a full pass; tell the person, then '
               f'{ctx.cli} release {first_rva} --reason "<one line>"'
               + (f', or continue with a stronger model ({ctx.cli} start {first_rva} --profile full)'
                  if prof['name'] == 'cheap' else ''))
    if summary['practice'] and passed == len(results):
        nxt = f'{ctx.cli} next'
    return (OK if passed == len(results) else FAILED), summary, nxt


def cmd_compare(ctx, args):
    return run_compare(ctx, args.task)


# ------------------------------------------------------------------ intake rules and submit

def changed_files(ctx, base, head='HEAD'):
    out = git(ctx, 'diff', '--name-status', '--no-renames', f'{base}...{head}' if head else base)
    rows = []
    for line in out.splitlines():
        status, _, name = line.partition('\t')
        rows.append((status[:1], name))
    return rows


def git_blob(ctx, ref, name):
    proc = ctx.run(['git', 'show', f'{ref}:{name}'], cwd=ctx.repo, capture_output=True)
    return proc.stdout if proc.returncode == 0 else None


def intake_problems(ctx, base, head='HEAD', files=None):
    """Contributor-scope rules on a diff, reading file contents from git (never executing them):
    only reconstruction unit files, a size cap and the source lint. Sibling (FNV) material is
    allowed on the Drafters' terms; the lint checks its SIBLING(...) labels and `Sibling source:`
    lines, and submit's label and origin checks read the clone when it is present."""
    import lint_reconstruction as lint
    problems = []
    rows = files if files is not None else changed_files(ctx, base, head)
    target = target_manifest(ctx.repo)['build_id']
    for status, name in rows:
        if not UNIT_PATH.fullmatch(name):
            problems.append(f'{name}: outside contributor scope (reconstruction/<area>/<Class>.h or .cpp only)')
            continue
        if status == 'D':
            problems.append(f'{name}: deleting a unit file is for maintainers')
            continue
        blob = git_blob(ctx, head, name) if head else (ctx.repo / name).read_bytes()
        if blob is None:
            problems.append(f'{name}: not readable at {head}')
            continue
        if len(blob) > MAX_UNIT_FILE_BYTES:
            problems.append(f'{name}: {len(blob)} bytes, over the {MAX_UNIT_FILE_BYTES}-byte contributor cap')
    # Lint the files as they would be integrated, in a temporary tree holding the head versions of
    # what the lint reads (sources, recipes, evidence files), so the working tree is never trusted.
    names = [n for s, n in rows if UNIT_PATH.fullmatch(n) and s != 'D']
    if names:
        import tempfile
        dirs = ('builds', 'reconstruction', 'findings', 'reports')
        if head:
            listed = git(ctx, 'ls-tree', '-r', '--name-only', head, *dirs).splitlines()
        else:
            listed = git(ctx, 'ls-files', *dirs).splitlines() + names
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in dict.fromkeys(listed):
                blob = git_blob(ctx, head, rel) if head else \
                    ((ctx.repo / rel).read_bytes() if (ctx.repo / rel).is_file() else None)
                if blob is None:
                    continue
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_bytes(blob)
            for n in names:
                problems += lint.lint_file(root, n, target)
    return problems


def cmd_intake(ctx, args):
    base = args.base
    problems = intake_problems(ctx, base, args.head)
    for p in problems:
        ctx.say(f'problem: {p}')
    ctx.say('intake: ' + ('PASS' if not problems else f'FAIL ({len(problems)} problem(s))'))
    return (OK if not problems else FAILED), {'problems': problems}, None if not problems else 'fix the problems listed'


def upstream_remote(ctx):
    """(upstream remote name or None, push remote name or None)."""
    up, push = None, None
    slug = (ctx.env.get('SR_UPSTREAM') or UPSTREAM).lower()
    for line in git(ctx, 'remote', '-v', check=False).splitlines():
        parts = line.split()
        if len(parts) < 3 or parts[2] != '(push)':
            continue
        name, url = parts[0], parts[1].lower().removesuffix('.git')
        if url.endswith(slug):
            up = up or name
        else:
            push = push or name
    return up, push


def pr_body(ctx, task, summary, args, labels, origin):
    template = (ctx.repo / '.github/PULL_REQUEST_TEMPLATE/function.md').read_text()
    rows = '\n'.join(f'| `{r["rva"]}` | `{r["name"]}` | {r["result"]} | `{r["reason"]}` | {r["candidate_size"]}/'
                     f'{r["target_size"]} | `{(r["code_section_sha256"] or "")[:16]}` |' for r in summary['functions'])
    report = {k: summary[k] for k in ('unit', 'source_revision', 'recipe', 'recipe_sha256', 'compiler',
                                      'image_sha256_pinned', 'comparator', 'contract_version')}
    report['functions'] = [{k: r[k] for k in ('rva', 'result', 'reason', 'candidate_size', 'target_size',
                                              'coverage', 'code_section_sha256')} for r in summary['functions']]
    fields = {
        'functions_table': rows,
        'report_json': json.dumps(report, indent=1),
        'drafted_by': args.drafted_by or load_config(ctx).get('drafted_by') or 'not stated',
        'label_findings': '\n'.join(f'- {x}' for x in labels) or '- none',
        'origin_findings': '\n'.join(f'- {x}' for x in origin) or '- none',
        'tool_revision': git(ctx, 'rev-parse', '--short=12', 'HEAD', check=False) or 'unknown',
    }
    for k, v in fields.items():
        template = template.replace('{{' + k + '}}', v)
    return template


def cmd_submit(ctx, args):
    tdir, task = load_task(ctx, args.task)
    practice = task.get('contrib', {}).get('practice')
    blockers, warnings = [], []
    try:
        summary = json.loads((tdir / 'last-compare.json').read_text())
    except (OSError, ValueError):
        raise Stop(USAGE, 'no comparison yet', f'{ctx.cli} compare')
    from source_digest import include_closure, tu_digest
    digest = tu_digest(ctx.repo, include_closure(ctx.repo, task['compiled']))
    if digest != summary['source_revision']:
        blockers.append('the unit changed since the last compare')
    if not all(r['result'] == 'pass' for r in summary['functions']):
        blockers.append('not every function passed the last compare')
    if summary['compiler'] != 'pinned':
        blockers.append('the last compare used a stand-in compiler, not the pinned MSVC')
    if practice:
        blockers.append('practice tasks re-do accepted functions and are not submitted')
    unit = [n for n in task['contrib']['unit'] if (ctx.repo / n).is_file()]
    up, push = upstream_remote(ctx)
    base = args.base or (f'{up}/main' if up else 'origin/main')
    if ctx.run(['git', 'rev-parse', '--verify', '--quiet', base], cwd=ctx.repo, capture_output=True).returncode != 0:
        base = 'HEAD'
    # Everything the branch would bring, not only the unit: committed changes since the base plus
    # the unit as it is on disk now.
    branch_rows = changed_files(ctx, base, 'HEAD') if base != 'HEAD' else []
    files = list(dict.fromkeys([(s, n) for s, n in branch_rows if n not in unit] + [('M', n) for n in unit]))
    problems = intake_problems(ctx, base, head=None, files=files)
    blockers += problems
    import check_labels
    import check_origin
    labels = check_labels.check([ctx.repo / n for n in unit], root=ctx.repo)
    warnings += [f'label: {x}' for x in labels]
    clones, missing = check_origin.open_clones(ctx.repo)
    hits = check_origin.check_unit([ctx.repo / n for n in unit], clones, root=ctx.repo)
    origin = [check_origin.describe(h) for h in hits]
    if any(not h['trivial'] and not h['fork_of'] and not h['declared'] for h in hits):
        blockers.append('a body close to a community body is not declared in the unit header '
                        '(docs/drafter-card.md, "Declare adapted bodies")')
    if missing:
        warnings.append('origin check ran without: ' + ', '.join(missing))
    full = ctx.run([sys.executable, str(ctx.repo / 'tools/check.py')], cwd=ctx.repo, capture_output=True, text=True)
    if full.returncode != 0:
        blockers.append('tools/check.py: ' + (full.stderr or full.stdout).strip()[-300:])
    try:
        open_items = ctx.github().open_items()
        me = ctx.github().user()
        own_urls = {c.get('url') for c in local_claims(ctx).values()}
        for fn in task['functions']:
            items = [i for i in open_items.get(parse_rva(fn['rva']), []) if i['url'] not in own_urls]
            _mine, fresh, _stale = claim_state(items, me)
            if fresh and not args.ack_collision:
                blockers.append(f'another open claim or pull request names {fn["rva"]}: '
                                + ', '.join(i['url'] for i in fresh) + ' (talk to them, or pass --ack-collision)'
                                + ('' if me else '; if it is yours, give claim --github-user <your-login>'))
    except Offline:
        warnings.append('GitHub not reachable: claims not checked')
    body = pr_body(ctx, task, summary, args, labels, origin)
    names = ', '.join(r['name'] for r in summary['functions'])
    title = f'Reconstruct {names} ({", ".join(r["rva"] for r in summary["functions"])})'
    (tdir / 'pr-body.md').write_text(body)
    for w in warnings:
        ctx.say(f'warning: {w}')
    for b in blockers:
        ctx.say(f'BLOCKED: {b}')
    drafted = args.drafted_by or load_config(ctx).get('drafted_by') or 'not stated'
    data = {'title': title, 'body_file': str(tdir / 'pr-body.md'), 'files': unit, 'blockers': blockers,
            'warnings': warnings, 'dry_run': bool(args.dry_run), 'base': base,
            'commit_message': f'{title}\n\nDrafted by {drafted}. Local comparator pass with the pinned recipe; '
                              'not yet confirmed by the project.'}
    ctx.say('A local pass is not acceptance: the project re-runs the comparison on two of its own hosts and a '
            'Reviewer checks the source before the function is recorded as matched.')
    if args.dry_run:
        plan = [f'git add {" ".join(unit)}', 'python3 tools/check.py --staged',
                f'git commit -m "{title}" -- {" ".join(unit)}',f'git push {push or "<your fork remote>"} HEAD',
                f'gh pr create --repo {ctx.github().repo} --title "{title}" --body-file {tdir / "pr-body.md"}']
        for p in plan:
            ctx.say(f'would run: {p}')
        return (OK if not blockers else FAILED), dict(data, plan=plan), \
            ('fix the blockers listed' if blockers else f'{ctx.cli} submit')
    if blockers:
        raise Stop(FAILED, f'{len(blockers)} blocker(s); nothing committed or pushed', 'fix the blockers listed', **data)
    other = [n for n in git(ctx, 'diff', '--cached', '--name-only').splitlines() if n and n not in unit]
    if other:
        raise Stop(USAGE, 'other files are staged: ' + ', '.join(other[:5]) + '; submit commits only the unit',
                   'git restore --staged <those files>, then submit again', **data)
    git(ctx, 'add', '--', *unit)
    staged = ctx.run([sys.executable, str(ctx.repo / 'tools/check.py'), '--staged'], cwd=ctx.repo,
                     capture_output=True, text=True)
    if staged.returncode != 0:
        raise Stop(FAILED, 'tools/check.py --staged: ' + (staged.stderr or staged.stdout).strip()[-300:])
    git(ctx, 'commit', '-m', data['commit_message'], '--', *unit)
    if not push:
        raise Stop(USAGE, 'no fork remote to push to', 'fork the repository on GitHub, then '
                   'git remote add fork https://github.com/<you>/skyrim-research.git and run submit again', **data)
    branch = git(ctx, 'rev-parse', '--abbrev-ref', 'HEAD')
    git(ctx, 'push', '-u', push, branch)
    task['contrib']['submitted'] = branch
    (tdir / 'task.json').write_text(json.dumps(task, indent=2) + '\n')
    gh = ctx.github().gh()
    if gh:
        owner = git(ctx, 'remote', 'get-url', push).rstrip('/').removesuffix('.git').replace(':', '/').split('/')[-2]
        proc = ctx.run([gh, 'pr', 'create', '--repo', ctx.github().repo, '--head', f'{owner}:{branch}',
                        '--title', title, '--body-file', str(tdir / 'pr-body.md')], capture_output=True, text=True)
        if proc.returncode == 0:
            url = proc.stdout.strip().splitlines()[-1]
            ctx.say(f'pull request: {url}')
            return OK, dict(data, pull_request=url), 'wait for the project to confirm; watch the pull request'
    link = f'https://github.com/{ctx.github().repo}/compare/main...{branch}?expand=1'
    ctx.say(f'open this link and paste {tdir / "pr-body.md"} as the description: {link}')
    return OK, dict(data, link=link), 'open the link and create the pull request'


# ------------------------------------------------------------------ go

def cmd_go(ctx, args):
    """setup -> next -> claim -> start, stopping at the first step that needs a person."""
    setup_args = argparse.Namespace(exe=args.exe, accept_microsoft_license=args.accept_microsoft_license,
                                    no_install=False, no_sources=False, no_self_test=args.no_self_test,
                                    steamcmd=False, no_sibling=args.no_sibling,
                                    accept_winget_source_agreements=args.accept_winget_source_agreements)
    try:
        cmd_setup(ctx, setup_args)
    except Stop as exc:
        # Drafting can begin before the compiler is installed; the executable is needed for the pack.
        if exc.code == MISSING and 'SkyrimSE.exe' not in exc.message and 'not the pinned' not in exc.message:
            ctx.say(f'continuing without a compiler for now: {exc.message}')
        else:
            raise
    if not args.rva:
        # Resume unfinished work instead of claiming a second function.
        base = ctx.private / 'tasks'
        for path in sorted(base.glob('*/task.json')) if base.is_dir() else []:
            task = json.loads(path.read_text())
            if not task.get('contrib', {}).get('practice') and not task['contrib'].get('submitted'):
                ctx.say(f'resuming {task["task_id"]} ({task["compiled"]})')
                return OK, {'task': task['task_id'], 'unit': task['contrib']['unit'], 'resumed': True}, \
                    f'edit {task["compiled"]}, then {ctx.cli} compare {task["task_id"]}'
    if args.rva:
        rva = args.rva
    else:
        _c, data, _n = cmd_next(ctx, argparse.Namespace(count=1, max_size=args.max_size))
        if not data['candidates']:
            raise Stop(OK, 'no startable function found')
        rva = data['candidates'][0]['rva']
    cmd_claim(ctx, argparse.Namespace(rva=rva, take_over=False, offline_ok=args.offline_ok))
    return start(ctx, argparse.Namespace(rva=[rva], practice=False, drafted_by=args.drafted_by, area=None,
                                         no_branch=args.no_branch, recipe=None, force=False, profile=args.profile))


# ------------------------------------------------------------------ main

def parser():
    p = argparse.ArgumentParser(prog='contrib.py', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--json', action='store_true', help='one JSON object on stdout; never prompts')
    p.add_argument('--yes', action='store_true', help='agree to package installs (never to a licence)')
    p.add_argument('--redact', action='store_true',
                   help='replace the checkout and home paths in all output; use it for anything you post publicly')
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('doctor')
    s.add_argument('--exe')
    s = sub.add_parser('setup')
    s.add_argument('--exe')
    s.add_argument('--accept-microsoft-license', action='store_true',
                   help='a person has read and accepted the VS 2017 Build Tools licence')
    s.add_argument('--no-install', action='store_true', help='print package commands instead of running them')
    s.add_argument('--no-sources', action='store_true')
    s.add_argument('--no-sibling', action='store_true', help='skip the optional FNV decompilation clone (about 175 MB)')
    s.add_argument('--no-self-test', action='store_true')
    s.add_argument('--steamcmd', action='store_true', help="also install Valve's SteamCMD")
    s.add_argument('--accept-winget-source-agreements', action='store_true',
                   help="Windows: a person has accepted the terms of winget's package source")
    s = sub.add_parser('next')
    s.add_argument('--count', type=int, default=5)
    s.add_argument('--max-size', type=int, default=64)
    s = sub.add_parser('claim')
    s.add_argument('rva', nargs='*')
    s.add_argument('--class', dest='classes', action='append', default=[])
    s.add_argument('--list', dest='lists', action='append', default=[])
    s.add_argument('--range', dest='ranges', action='append', default=[])
    s.add_argument('--take-over', action='store_true')
    s.add_argument('--offline-ok', action='store_true')
    s.add_argument('--github-user', help='your GitHub login, when gh is not signed in')
    s = sub.add_parser('release')
    s.add_argument('rva')
    s.add_argument('--reason')
    s = sub.add_parser('start')
    s.add_argument('rva', nargs='+')
    s.add_argument('--drafted-by')
    s.add_argument('--area')
    s.add_argument('--recipe')
    s.add_argument('--practice', action='store_true', help='try an already matched function as an exercise')
    s.add_argument('--profile', choices=CONTRIB_PROFILES,
                   help='cheap (default: small card, Haiku/Luna-class) or full (full card, Sonnet-class); never changes the gate')
    s.add_argument('--no-branch', action='store_true')
    s.add_argument('--force', action='store_true', help=argparse.SUPPRESS)
    s = sub.add_parser('compare')
    s.add_argument('task', nargs='?')
    s = sub.add_parser('submit')
    s.add_argument('task', nargs='?')
    s.add_argument('--dry-run', action='store_true')
    s.add_argument('--base')
    s.add_argument('--drafted-by')
    s.add_argument('--ack-collision', action='store_true')
    s = sub.add_parser('intake')
    s.add_argument('--base', required=True)
    s.add_argument('--head', default='HEAD')
    s = sub.add_parser('go')
    s.add_argument('rva', nargs='?')
    s.add_argument('--exe')
    s.add_argument('--drafted-by')
    s.add_argument('--accept-microsoft-license', action='store_true')
    s.add_argument('--accept-winget-source-agreements', action='store_true')
    s.add_argument('--no-sibling', action='store_true')
    s.add_argument('--no-self-test', action='store_true')
    s.add_argument('--no-branch', action='store_true')
    s.add_argument('--offline-ok', action='store_true')
    s.add_argument('--max-size', type=int, default=64)
    s.add_argument('--profile', choices=CONTRIB_PROFILES,
                   help='cheap (default: small card, Haiku/Luna-class) or full (full card, Sonnet-class); never changes the gate')
    return p


COMMANDS = {'doctor': cmd_doctor, 'setup': cmd_setup, 'next': cmd_next, 'claim': cmd_claim, 'release': cmd_release,
            'start': cmd_start, 'compare': cmd_compare, 'submit': cmd_submit, 'intake': cmd_intake, 'go': cmd_go}


def main(argv=None, ctx=None):
    args = parser().parse_args(argv)
    ctx = ctx or Ctx(as_json=args.json, assume_yes=args.yes)
    ctx.as_json = ctx.as_json or args.json
    ctx.interactive = ctx.interactive and not ctx.as_json
    ctx.assume_yes = ctx.assume_yes or args.yes
    ctx.redact = ctx.redact or args.redact
    apply_wine_env(ctx)
    try:
        code, data, nxt = COMMANDS[args.command](ctx, args)
        message = None
    except Stop as exc:
        code, data, nxt, message = exc.code, exc.data, exc.next_action, exc.message
        if not ctx.as_json:
            print(ctx.scrub(f'{"error" if code else "note"}: {message}'), file=sys.stderr)
            for line in data.get('steamcmd_route') or []:
                print(ctx.scrub(f'  {line}'), file=sys.stderr)
            for line in data.get('errors') or []:
                print(ctx.scrub(f'  {line}'), file=sys.stderr)
    if ctx.as_json:
        out = {'command': args.command, 'ok': code == OK, 'exit_code': code, 'error': message, 'next': nxt}
        out.update({k: v for k, v in (data or {}).items() if k not in out})
        out['messages'] = ctx.log
        print(ctx.scrub(json.dumps(out, indent=2, default=str)))
    elif nxt:
        print(ctx.scrub(f'next: {nxt}'))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
