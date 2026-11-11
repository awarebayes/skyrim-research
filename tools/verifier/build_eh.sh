#!/usr/bin/env bash
# Compile and link the synthetic comparator-v2 sources into a fresh output directory.
#
# Usage: build_eh.sh <msvc-install-dir> <output-dir>
# eh_cases.cpp uses the first recipe's flags (as build_pilot.sh does); eh_gs.cpp adds /GS so
# the security-cookie handler shapes appear, which that recipe (/GS-) never produces.
set -euo pipefail

MSVC=$1
OUT=$2
SRC=$(cd "$(dirname "$0")/synthetic" && pwd)

CFLAGS=(/nologo /c /O2 /MD /GS- /EHsc /GR /fp:precise /Gy)
GSFLAGS=(/nologo /c /O2 /MD /GS /EHsc /GR /fp:precise /Gy)
LFLAGS=(/nologo /DLL /MACHINE:X64 /INCREMENTAL:NO /OPT:REF /OPT:ICF /DEBUG)

if [ -e "$OUT" ]; then
    echo "output directory already exists: $OUT" >&2
    exit 1
fi
mkdir -p "$OUT"
cd "$OUT"

"$MSVC/bin/x64/cl" "${CFLAGS[@]}" /Foeh_cases.obj "$SRC/eh_cases.cpp"
"$MSVC/bin/x64/cl" "${GSFLAGS[@]}" /Foeh_gs.obj "$SRC/eh_gs.cpp"
"$MSVC/bin/x64/link" "${LFLAGS[@]}" /OUT:eh.dll /MAP:eh.map /PDB:eh.pdb eh_cases.obj eh_gs.obj

{
    printf 'cflags'; printf ' %s' "${CFLAGS[@]}"; printf '\n'
    printf 'gsflags'; printf ' %s' "${GSFLAGS[@]}"; printf '\n'
    printf 'lflags'; printf ' %s' "${LFLAGS[@]}"; printf '\n'
} > flags.txt
sha256sum eh_cases.obj eh_gs.obj eh.dll eh.map > outputs.sha256
cat outputs.sha256
