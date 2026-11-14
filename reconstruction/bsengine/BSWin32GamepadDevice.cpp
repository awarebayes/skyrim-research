// BSWin32GamepadDevice functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bswin32gamepaddevice
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xe7b050, 3 bytes: BSWin32GamepadDevice::Release
//   RVA 0xe7b080, 3 bytes: BSWin32GamepadDevice::SetRumble
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSWin32GamepadDevice.h"

// RVA 0xe7b050, 3 bytes
void BSWin32GamepadDevice::Release()
{
}

// RVA 0xe7b080, 3 bytes
void BSWin32GamepadDevice::SetRumble(float lValue, float rValue)
{
}
