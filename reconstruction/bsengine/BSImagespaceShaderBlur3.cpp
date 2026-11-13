// BSImagespaceShaderBlur3 functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s17-nirefobject-bsimagespaceshaderblur3
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1507e00, 52 bytes: BSImagespaceShaderBlur3::~BSImagespaceShaderBlur3 (scalar deleting destructor)
//   RVA 0x1509cb0, 57 bytes: BSImagespaceShaderBlur3::Unk_0D
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSImagespaceShaderBlur3.h"

// Not compared on its own: the compiler emits the vftable here, and with it the deleting
// destructor that is compared. The destructor itself stays undefined here so that the compiler
// calls the separate complete destructor, as the listing does.
BSImagespaceShaderBlur3::BSImagespaceShaderBlur3()
{
}

BSImagespaceShaderBlur3Table BSImagespaceShaderBlur3::Unk_0D()
{
    BSImagespaceShaderBlur3Table table;
    table.name00 = "TEXTAP";
    table.data08 = &g_blurDataA;
    table.name10 = "COLORRANGE";
    table.data18 = &g_blurDataB;
    table.ptr20 = nullptr;
    table.ptr28 = nullptr;
    return table;
}
