// BSMemStorage::GetFileSize, build sse-steam-1-7-104, RVA 0xec1710, 4 bytes.
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
// BSMemStorage: EXE_RTTI
// GetFileSize: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// member, padding: GUESS(low); storage names invented for the measured member offset
#pragma once
#include <cstddef>
#include <cstdint>
// GetFileSize: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
class BSMemStorage
{
public:
    virtual std::uint32_t GetFileSize() const;
    // GetPosition: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); signature from the sheet, not checked against the community header
    virtual std::size_t GetPosition() const;
    // ~BSMemStorage: GUESS(low); declared out of line, the deleting destructor calls the plain one at RVA 0xec16c0, bound by hint
    BSMemStorage();
    virtual ~BSMemStorage();
    std::uint8_t padding[0x18];
    std::uint32_t member;
    // position: GUESS(low); the offset GetPosition reads
    std::uint32_t position;    // 24
    // unk28: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); padding to the 0x30 size
    std::uint8_t  unk28[0x8];  // 28
};
static_assert(sizeof(BSMemStorage) == 0x30, "layout");
