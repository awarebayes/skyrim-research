#!/usr/bin/env bash
# Build original synthetic TU-local initializer/teardown fixtures; outputs stay private.
# Usage: build_static.sh <msvc-install-dir> <new-output-dir-under-.local>
set -euo pipefail
MSVC=$1
OUT=$(python3 -c 'import pathlib,sys
p = pathlib.Path(sys.argv[1]).resolve()
if not any(parent.name == ".local" for parent in p.parents):
    raise SystemExit("output must resolve under .local/")
print(p)' "$2")
SRC=$(cd "$(dirname "$0")/synthetic" && pwd)
if [ -e "$OUT" ]; then
    echo 'output directory already exists' >&2
    exit 1
fi
mkdir -p "$OUT"
cd "$OUT"
for unit in static_identity_a static_identity_b static_identity_runtime; do
    "$MSVC/bin/x64/cl" /nologo /c /O2 /MD /GS- /EHsc /GR /fp:precise /Gy "/Fo$unit.obj" "$SRC/$unit.cpp"
done
"$MSVC/bin/x64/link" /nologo /DLL /NOENTRY /NODEFAULTLIB /MACHINE:X64 /INCREMENTAL:NO /OPT:NOREF /OPT:NOICF /MAP:static.map /OUT:static.dll static_identity_a.obj static_identity_b.obj static_identity_runtime.obj
