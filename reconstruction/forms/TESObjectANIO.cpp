// TESObjectANIO functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-tesobjectanio
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/fifth-batch-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x27bb70, 19 bytes: TESObjectANIO::GetFormEditorID
//   RVA 0x27b9b0, 52 bytes: TESObjectANIO::InitItemImpl
// Adapted bodies: none (write "none" when attempt prints no "origin advice" line;
// otherwise name each adapted body, its upstream file, revision and licence).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESObjectANIO.h"

const char* TESObjectANIO::GetFormEditorID() const
{
    return editorID ? editorID : g_defaultFormEditorIDString;
}

