// TESPackage::IsPackageOwner, build sse-steam-1-7-104, RVA 0x49e8e0, 3 bytes.
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
// Task p92-s-tespackage: declarations for RVA 0x49e8d0, 0x49e270 and 0x49e890 added beside IsPackageOwner.
// Base form: shared header ../forms/TESForm.h for TESForm (sizeof 0x20).
// TESPackage: EXE_RTTI
// TESPackage::GetRefCount, TESPackage::GetObjectTypeName, TESPackage::~TESPackage: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// IsPackageOwner: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// objectType, unknown20, unknown25: GUESS(low); measured from the listings, names invented
#pragma once
#include <cstdint>
#include "../forms/TESForm.h"
class TESPackage : public TESForm
{
public:
    TESPackage();
    // IsPackageOwner: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
    virtual std::uint8_t IsPackageOwner() const;
    virtual std::uint32_t GetRefCount() const;
    virtual const char* GetObjectTypeName() const;
    virtual ~TESPackage();

private:
    // unknown20: GUESS(low); padding from the base end to the field at 0x24
    std::uint8_t unknown20[0x4];
    // objectType: GUESS(low); byte at 0x24, sign-extended and used as the table index
    std::int8_t objectType;
    // unknown25: GUESS(low); padding from 0x25 to 0xDB
    std::uint8_t unknown25[0xb7];
    // refCount: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); dword at 0xDC
    std::uint32_t refCount;
};
static_assert(sizeof(TESPackage) == 0xe0, "TESPackage size");
