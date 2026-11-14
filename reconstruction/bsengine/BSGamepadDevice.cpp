// BSGamepadDevice functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsgamepaddevice
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xcfbde0, 3 bytes: BSGamepadDevice::Unk_0E
//   RVA 0xcfc180, 3 bytes: BSGamepadDevice::Unk_0C
//   RVA 0xcfc1a0, 3 bytes: BSGamepadDevice::ResetLEDColor
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSGamepadDevice.h"

// RVA 0xcfbde0, 3 bytes
void BSGamepadDevice::Unk_0E()
{
}

// RVA 0xcfc180, 3 bytes
bool BSGamepadDevice::Unk_0C()
{
    return false;
}

// RVA 0xcfc1a0, 3 bytes
void BSGamepadDevice::ResetLEDColor()
{
}
