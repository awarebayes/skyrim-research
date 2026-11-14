// Script functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-script
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/p92-unit-supply-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by haiku-202611131358-1 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x344760, 8 bytes: Script::InitItemImpl
//   RVA 0x3463a0, 8 bytes: Script::GetProcessScripts
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "Script.h"

// g_scriptProcessScripts: GUESS(low); a mutable global the compared GetProcessScripts reads at 0x207e511
extern bool g_scriptProcessScripts;
// ScriptInitItemHelper: GUESS(low); the target tail-jumps to it with this passed twice, at 0x344770
void ScriptInitItemHelper(Script* a_self, Script* a_other);

void Script::InitItemImpl()
{
    ScriptInitItemHelper(this, this);
}

bool Script::GetProcessScripts()
{
    return g_scriptProcessScripts;
}
