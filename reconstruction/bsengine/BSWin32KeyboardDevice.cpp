// BSWin32KeyboardDevice functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bswin32keyboarddevice
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by haiku-202611131358-4 (claude-haiku-5-5), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xe12c20, 3 bytes: BSWin32KeyboardDevice::Unk_09
//   RVA 0xe12c30, 3 bytes: BSWin32KeyboardDevice::Unk_0A
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSWin32KeyboardDevice.h"

// RVA 0xe12c20, 3 bytes, BSWin32KeyboardDevice::Unk_09.
void BSWin32KeyboardDevice::Unk_09()
{
}

// RVA 0xe12c30, 3 bytes, BSWin32KeyboardDevice::Unk_0A.
void BSWin32KeyboardDevice::Unk_0A()
{
}
