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
// Task p92-s-tespackage: bodies for RVA 0x49e8d0 and 0x49e270 and the empty-body constructor added beside IsPackageOwner.
// Evidence: findings/fifth-batch-selection.md
// Drafted by claude-haiku-5-5 (Claude Haiku 5.5), drafter label haiku-202611131358-2.
// Adapted bodies for the new functions: none; each body is written from its listing.
// TESPackageObjectTypeNames: GUESS(low); a table of pointers indexed by objectType, bound by address through bind-hints.json.
// TESPackage::TESPackage: GUESS(low); constructor name from the class name, body empty
// TESPackage::GetRefCount, TESPackage::GetObjectTypeName: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#include "TESPackage.h"

extern const char* const TESPackageObjectTypeNames[];

// Not compared: defined so that the compiler emits the vftable and the deleting destructor beside it.
TESPackage::TESPackage()
{
}

// IsPackageOwner: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
std::uint8_t TESPackage::IsPackageOwner() const
{
    return 0x1;
}

std::uint32_t TESPackage::GetRefCount() const
{
    return refCount;
}

const char* TESPackage::GetObjectTypeName() const
{
    return TESPackageObjectTypeNames[objectType];
}
