#!/usr/bin/env bash
# Compile and link the synthetic pilot sources once into a fresh output directory.
# Run it twice with different output directories to test determinism.
#
# Usage: build_pilot.sh <msvc-install-dir> <output-dir>
# The output directory must not exist yet, so every build starts clean.
set -euo pipefail

MSVC=$1
OUT=$2
SRC=$(cd "$(dirname "$0")/synthetic" && pwd)

# First-choice codegen flags from findings/compiler-candidates.md; no /GL, no debug info in
# objects (/Zi or /Z7 change object metadata, not code).
CFLAGS=(/nologo /c /O2 /MD /GS- /EHsc /GR /fp:precise /Gy)
# A DLL keeps the exported functions alive under /OPT:REF; /DEBUG adds a CodeView record so
# the determinism check sees the same kind of debug directory the target carries.
LFLAGS=(/nologo /DLL /MACHINE:X64 /INCREMENTAL:NO /OPT:REF /OPT:ICF /DEBUG)

if [ -e "$OUT" ]; then
    echo "output directory already exists: $OUT" >&2
    exit 1
fi
mkdir -p "$OUT"
cd "$OUT"

"$MSVC/bin/x64/cl" "${CFLAGS[@]}" /Fopilot.obj "$SRC/pilot.cpp"
"$MSVC/bin/x64/cl" "${CFLAGS[@]}" /Fopilot_variant.obj "$SRC/pilot_variant.cpp"
"$MSVC/bin/x64/link" "${LFLAGS[@]}" /OUT:pilot.dll /MAP:pilot.map /PDB:pilot.pdb pilot.obj

{
    printf 'cflags'; printf ' %s' "${CFLAGS[@]}"; printf '\n'
    printf 'lflags'; printf ' %s' "${LFLAGS[@]}"; printf '\n'
} > flags.txt
sha256sum pilot.obj pilot_variant.obj pilot.dll pilot.pdb pilot.map > outputs.sha256
cat outputs.sha256
