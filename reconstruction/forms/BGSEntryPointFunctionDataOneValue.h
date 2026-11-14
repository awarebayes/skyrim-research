// BGSEntryPointFunctionDataOneValue::GetType, build sse-steam-1-7-104, RVA 0x38eeb0, 6 bytes.
// Labels: v2
// Source exposure: mixed (local binary analysis and public names).
// Evidence: findings/generator-leaves-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Drafted by tools/stamp.py (Codex GPT-6.1 Sol).
// Origin: {"generator_family":"const-return","generator_version":"2","name_source":{"confidence":"medium","kind":"public","repository":"meh321/AddressLibraryDatabase","revision":"0379cb6fdaa0d68e69ef9ad1a2d39caa6611ac91","source":"meh321"},"template_digest":"df32415c55896040a11705484c0f0da5801925ec042c4cc3a23c954179756459"}
// Only the named leaf is compared. Types are minimal stand-ins; names are unverified.
// Adapted bodies: none. Body synthesized from the bounded leaf template.
// A comparator pass verifies code under the recipe, not names or original source form.
// Reconstruction carries no general licence grant; see LEGAL.md and PROVENANCE.md.
// BGSEntryPointFunctionDataOneValue: EXE_RTTI
// GetType: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// member, padding: GUESS(low); storage names invented for the measured member offset
#pragma once
#include <cstdint>
// GetType: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// BGSEntryPointFunctionData: GUESS(low); stand-in base whose vtable the deleting destructor stores after the derived one
class BGSEntryPointFunctionData
{
public:
    virtual ~BGSEntryPointFunctionData() {}  // 00
};

// BGSEntryPointFunctionDataOneValue: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); name only; the 16-byte object size the deleting destructor frees
class BGSEntryPointFunctionDataOneValue : public BGSEntryPointFunctionData
{
public:
    // BGSEntryPointFunctionDataOneValue::BGSEntryPointFunctionDataOneValue: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); name only; declared so the vftable and the deleting destructor are emitted in this unit
    BGSEntryPointFunctionDataOneValue();
    ~BGSEntryPointFunctionDataOneValue() override {}
    virtual std::uint32_t GetType() const;

    // unk08: GUESS(low); padding to the 0x10 size
    std::uint8_t unk08[0x8];  // 08
};
static_assert(sizeof(BGSEntryPointFunctionDataOneValue) == 0x10, "layout");
