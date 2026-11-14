// BSVirtualKeyboardDevice functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsvirtualkeyboarddevice
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xe7c4b0, 3 bytes: BSVirtualKeyboardDevice::Unk_09
//   RVA 0xe7c4c0, 3 bytes: BSVirtualKeyboardDevice::Unk_0A
//   RVA 0xe7c4d0, 62 bytes: BSVirtualKeyboardDevice::~BSVirtualKeyboardDevice
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSVirtualKeyboardDevice.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
BSVirtualKeyboardDevice::BSVirtualKeyboardDevice()
{
}

// Unk_09: the target has no work to do.
void BSVirtualKeyboardDevice::Unk_09()
{
}

// Unk_0A: the target has no work to do.
void BSVirtualKeyboardDevice::Unk_0A()
{
}
