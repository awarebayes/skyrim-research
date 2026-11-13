// TESObjectWEAP functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q1-s01-tesboundobject-tesobjectweap
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-1-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x28e7f0, 19 bytes: TESObjectWEAP::GetObjectTypeName
//   RVA 0x28e7b0, 24 bytes: TESObjectWEAP::GetDescriptionOwnerFile
//   RVA 0x28e500, 52 bytes: TESObjectWEAP::~TESObjectWEAP
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "TESObjectWEAP.h"

// kObjectTypeNames: GUESS(low); the table of type name strings indexed by unk19D
extern const char* kObjectTypeNames[];

// ResolveOwnerFile: GUESS(low); the callee takes the form and a 32-bit index, and returns the file
TESFile* ResolveOwnerFile(const TESForm* a_form, std::uint32_t a_index);

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
TESObjectWEAP::TESObjectWEAP()
{
}

const char* TESObjectWEAP::GetObjectTypeName() const
{
    return kObjectTypeNames[static_cast<std::uint32_t>(unk19D)];
}

TESFile* TESObjectWEAP::GetDescriptionOwnerFile() const
{
    return ResolveOwnerFile(unknown208 != nullptr ? unknown208 : this, 0xFFFFFFFFu);
}
