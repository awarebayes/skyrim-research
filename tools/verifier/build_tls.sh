#!/usr/bin/env bash
# Compile and link the synthetic thread-local sources into a fresh output directory.
#
# Usage: build_tls.sh <msvc-install-dir> <output-dir>
# tls_cases.cpp is compiled and linked into tls.dll with the first recipe's flags (as
# build_eh.sh does); tls_variant.cpp is compiled only, as the perturbed candidate.
set -euo pipefail

MSVC=$1
OUT=$2
SRC=$(cd "$(dirname "$0")/synthetic" && pwd)

CFLAGS=(/nologo /c /O2 /MD /GS- /EHsc /GR /fp:precise /Gy)
LFLAGS=(/nologo /DLL /MACHINE:X64 /INCREMENTAL:NO /OPT:REF /OPT:ICF /DEBUG)

if [ -e "$OUT" ]; then
    echo "output directory already exists: $OUT" >&2
    exit 1
fi
mkdir -p "$OUT"
cd "$OUT"

"$MSVC/bin/x64/cl" "${CFLAGS[@]}" /Fotls_cases.obj "$SRC/tls_cases.cpp"
"$MSVC/bin/x64/cl" "${CFLAGS[@]}" /Fotls_variant.obj "$SRC/tls_variant.cpp"
"$MSVC/bin/x64/link" "${LFLAGS[@]}" /OUT:tls.dll /MAP:tls.map /PDB:tls.pdb tls_cases.obj

{
    printf 'cflags'; printf ' %s' "${CFLAGS[@]}"; printf '\n'
    printf 'lflags'; printf ' %s' "${LFLAGS[@]}"; printf '\n'
} > flags.txt
sha256sum tls_cases.obj tls_variant.obj tls.dll tls.map > outputs.sha256
cat outputs.sha256
