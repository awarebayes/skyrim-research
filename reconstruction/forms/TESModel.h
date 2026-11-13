// TESModel::GetModel, build sse-steam-1-7-104, RVA 0x146780, 5 bytes.
// Labels: v2
// Source exposure: mixed (local binary analysis and public names).
// Evidence: findings/generator-leaves-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Drafted by tools/stamp.py (Codex GPT-6.1 Sol).
// Origin: {"generator_family":"member-return","generator_version":"2","name_source":{"confidence":"medium","kind":"public","repository":"meh321/AddressLibraryDatabase","revision":"0379cb6fdaa0d68e69ef9ad1a2d39caa6611ac91","source":"meh321"},"template_digest":"1254832e5ca7cdca7f6330a2018dde32919625f6149744dd0138e59a943106d8"}
// Only the named leaf is compared. Types are minimal stand-ins; names are unverified.
// Adapted bodies: none. Body synthesized from the bounded leaf template.
// A comparator pass verifies code under the recipe, not names or original source form.
// Reconstruction carries no general licence grant; see LEGAL.md and PROVENANCE.md.
// TESModel: EXE_RTTI
// GetModel: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// member, padding: GUESS(low); storage names invented for the measured member offset
#pragma once
#include <cstdint>
// GetModel: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
class TESModelTextureSwap;

// TESModel::GetAsModelTextureSwap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); compared at RVA 0x1dfd80
class TESModel
{
public:
    virtual void* GetModel() const;
    virtual TESModelTextureSwap* GetAsModelTextureSwap();  // compared: 0x1dfd80
    void* member;
};
