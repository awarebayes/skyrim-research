// Build: sse-steam-1-7-104; RVA 0xa0d410; 43 bytes
// Evidence: findings/ghidra-import.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Source exposure: mixed (represented community declarations and local binary analysis).
// Drafted by tools/deleting_layout_leaf_v2.py (GPT-6.1 Sol).
// Labels: v2
// IGiftMenuScriptCallbackStorageLayout: GUESS(medium) STANDIN; represented layout type names.
// object: GUESS(low)
// Empty destructor bodies are inferred stand-ins for the compared leaf code only.
// Fields and inheritance come from the included represented layout, never an allocation-size array.
// No original field ownership or omitted methods are claimed; only scalar deleting code is compared.
// Shared structural template specializations do not recover original template arguments.
// The static objects request normal compiler emission; initialization and other methods are unassessed.
// Origin: {"family": "scalar-deleting-leaf", "template_digest": "c33e297cfc05a40c93d0a1165f3507172be2c064f498593ede6fbdb9cfba8eb5", "version": "2"}
// Declaration source: powerof3/CommonLibSSE@654e55f7979c1733033d5dbef176e43827bac944 include/RE/I/IGiftMenuScriptCallback.h; GPL-3.0.
void operator delete(void*, unsigned __int64) noexcept;
#include "IGiftMenuScriptCallbackStorageLayout.h"
namespace ResearchLayouts {
inline IGiftMenuScriptCallbackStorageLayout::~IGiftMenuScriptCallbackStorageLayout() {}
}
static_assert(sizeof(ResearchLayouts::IGiftMenuScriptCallbackStorageLayout) == 16, "independently observed allocation size");
static ResearchLayouts::IGiftMenuScriptCallbackStorageLayout object;
