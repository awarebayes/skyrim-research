// Build: sse-steam-1-7-104
// Evidence: findings/ghidra-import.md
// Source exposure: binary-analysis (RTTI inheritance and measured deletion sizes).
// Drafted by tools/adjustor_thunk_template_v3.py (GPT-6.1 Sol).
// Labels: v2
// Original declarations inferred from local RTTI; no external implementation copied.
// Only declared inheritance and sizes are represented; method sets remain incomplete.
// No data members or padding are introduced to force a size.
// Layout agreement is not a comparator match, behavior claim or original-source claim.
// RVA 0x83038c; 9 bytes
// RVA 0x830398; 9 bytes
// RVA 0x8303a4; 9 bytes
// RVA 0x8303b0; 9 bytes
// RVA 0x8303bc; 9 bytes
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Origin: {"family": "represented-adjustor-thunk", "template_digest": "197a5390162e8fa5e349274a6d522934c9bd50ae8d74d94f5983234388f85488", "version": "3"}
// The ordinary owner constructor initializes each product-registration base.
// Base registration operations and the owner destructor remain external.
// The constructor itself is outside the compared scope; only listed secondary destructor adjustors are compared.
// No added derived type, static object, helper body or emission-forcing attribute is used.
#include "AutoRegisterCombatMagicCasterSummonLayout.h"
namespace ResearchLayouts {
AutoRegisterCombatMagicCasterSummonLayout::AutoRegisterCombatMagicCasterSummonLayout() = default;
}
