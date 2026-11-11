#!/usr/bin/env bash
# Set up an MSVC v141 (VS 2017 15.9) x64 compiler under Wine on a fresh x86-64 Ubuntu 24.04
# machine. Every input is pinned: the msvc-wine commit, the Visual Studio installer manifest
# (by URL and SHA-256), and the resulting compiler binaries (by SHA-256, from pinned.sha256).
# Packages come only from Microsoft's servers, through URLs listed in that manifest; vsdownload.py
# checks each payload against the manifest's SHA-256 before unpacking.
#
# Running this script accepts the Microsoft Build Tools for Visual Studio 2017 licence on behalf
# of whoever runs it (vsdownload.py --accept-license). Only run it if that licence basis is
# recorded for your use.
#
# Usage: setup_boat_machine.sh [install-dir]       (default: $HOME/msvc)
# Needs: sudo for apt, about 4 GB free disk, network access to the Ubuntu archive, GitHub
# (public msvc-wine clone only, no credentials) and download.visualstudio.microsoft.com.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
DEST=${1:-$HOME/msvc}
WORK=${WORK:-$HOME/verifier-setup}

MSVC_WINE_URL=https://github.com/mstorsjo/msvc-wine.git
MSVC_WINE_COMMIT=d8a499efde3e1bd1862e2bebac976640c5f4c1fe
# Installer manifest for Visual Studio 2017 15.9.85, as listed by https://aka.ms/vs/15/release/channel.
# The channel always points at the newest 15.9 servicing release, so the manifest is pinned
# directly instead of following the channel.
VSMAN_URL=https://download.visualstudio.microsoft.com/download/pr/15e9c549-f982-4bd3-aa51-9c284bb7853d/78641af3bcff98bf1314136dcccf4ce252c301b9ef4d3cee1c66a086e787a47a/VisualStudio.vsman
VSMAN_SHA256=3f11dac605c9241ddb6b0ec8a374de97f778a75df93788e7e7ec417d1ea8ee17
SDK_VERSION=10.0.19041

log() { printf '== %s\n' "$*"; }

log "host"
uname -srm
grep -E '^(NAME|VERSION)=' /etc/os-release
grep -m1 'model name' /proc/cpuinfo || true
nproc

log "apt packages"
sudo DEBIAN_FRONTEND=noninteractive apt-get update -q
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends \
    wine wine64 python3 msitools ca-certificates winbind git curl unzip
dpkg-query -W -f='${Package} ${Version} ${Architecture}\n' wine wine64 2>/dev/null || true
dpkg-query -W -f='${Package} ${Version}\n' libwine msitools libgcab-1.0-0 winbind python3 2>/dev/null || true
WINE=$(command -v wine64 || command -v wine || true)
if [ -z "$WINE" ] && [ -x /usr/lib/wine/wine64 ]; then
    WINE=/usr/lib/wine/wine64
fi
[ -n "$WINE" ] || { echo "no wine binary found" >&2; exit 1; }
"$WINE" --version

log "msvc-wine at pinned commit"
mkdir -p "$WORK"
if [ ! -d "$WORK/msvc-wine/.git" ]; then
    git clone -q "$MSVC_WINE_URL" "$WORK/msvc-wine"
fi
git -C "$WORK/msvc-wine" -c advice.detachedHead=false checkout -q "$MSVC_WINE_COMMIT"
test "$(git -C "$WORK/msvc-wine" rev-parse HEAD)" = "$MSVC_WINE_COMMIT"
git -C "$WORK/msvc-wine" log -1 --format='%H %cI'

log "installer manifest"
curl -fsSL -o "$WORK/VisualStudio.vsman" "$VSMAN_URL"
echo "$VSMAN_SHA256  $WORK/VisualStudio.vsman" | sha256sum -c -

log "download and unpack toolset and SDK"
# Package selection: the default VC x86/x64 tools component of this manifest plus one SDK.
# The manifest offers no older 14.16 build as a separately named component, so the toolset
# build is whatever this pinned manifest ships; pinned.sha256 below is what detects a change.
rm -rf "$DEST"
( cd "$WORK" && python3 -I "$WORK/msvc-wine/vsdownload.py" \
    --manifest "$WORK/VisualStudio.vsman" --major 15 \
    --host-arch x64 --architecture x64 \
    --with-default no --with-msvc yes --with-sdk yes --sdk-version "$SDK_VERSION" \
    --accept-license --print-selection ) > "$WORK/selection.txt"
cat "$WORK/selection.txt"
( cd "$WORK" && python3 -I "$WORK/msvc-wine/vsdownload.py" \
    --manifest "$WORK/VisualStudio.vsman" --major 15 \
    --host-arch x64 --architecture x64 \
    --with-default no --with-msvc yes --with-sdk yes --sdk-version "$SDK_VERSION" \
    --accept-license --dest "$DEST" )

log "msvc-wine install.sh"
"$WORK/msvc-wine/install.sh" "$DEST"

log "toolset identity"
MSVCVER=$(ls "$DEST/VC/Tools/MSVC")
echo "toolset directory: $MSVCVER"
ls "$DEST/Windows Kits/10/Include"
BIN="$DEST/VC/Tools/MSVC/$MSVCVER/bin/Hostx64/x64"
( cd "$BIN" && sha256sum cl.exe c1xx.dll c2.dll link.exe && stat -c '%n %s' cl.exe c1xx.dll c2.dll link.exe )
WINEDEBUG=-all "$DEST/bin/x64/cl" 2>&1 | head -n 2 || true
WINEDEBUG=-all "$DEST/bin/x64/link" 2>&1 | head -n 2 || true

if [ -s "$HERE/pinned.sha256" ]; then
    log "check against pinned.sha256"
    ( cd "$BIN" && sha256sum -c "$HERE/pinned.sha256" )
else
    log "pinned.sha256 missing: hashes above are unverified"
    exit 3
fi
log "done: compiler at $DEST/bin/x64/cl"
