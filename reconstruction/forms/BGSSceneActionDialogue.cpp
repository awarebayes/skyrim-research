// BGSSceneActionDialogue functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s20-bgssceneaction-bgssceneactiondialogue
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by claude-haiku-5-5, starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x3ab280, 4 bytes: BGSSceneActionDialogue::GetEmotionType
//   RVA 0x3ab290, 4 bytes: BGSSceneActionDialogue::GetEmotionValue
//   RVA 0x3ab530, 7 bytes: BGSSceneActionDialogue::Loops
//   RVA 0x3ab2a0, 9 bytes: BGSSceneActionDialogue::FacesTarget
//   RVA 0x3abcf0, 19 bytes: BGSSceneActionDialogue::Unk_0B
//   RVA 0x3ab1c0, 43 bytes: BGSSceneActionDialogue::~BGSSceneActionDialogue (scalar deleting destructor)
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BGSSceneActionDialogue.h"

template <class T>
static T& RawAt(const void* a_base, std::ptrdiff_t a_offset)
{
    return *reinterpret_cast<T*>(const_cast<std::uint8_t*>(reinterpret_cast<const std::uint8_t*>(a_base)) + a_offset);
}

// Not compared on its own: the compiler emits the vftable here, and with it the deleting
// destructor that is compared.
BGSSceneActionDialogue::BGSSceneActionDialogue()
{
}

EmotionType BGSSceneActionDialogue::GetEmotionType() const
{
    return static_cast<EmotionType>(RawAt<std::uint32_t>(this, 0x38));
}

std::uint32_t BGSSceneActionDialogue::GetEmotionValue() const
{
    return RawAt<std::uint32_t>(this, 0x3c);
}

bool BGSSceneActionDialogue::Loops() const
{
    return RawAt<std::uint8_t>(this, 0x12) & 1;
}

bool BGSSceneActionDialogue::FacesTarget() const
{
    return (flags10 >> 0xF) & 1;
}

void BGSSceneActionDialogue::Unk_0B()
{
    flags10 &= 0xFFFFBFFF;
    RawAt<std::uint32_t>(this, 0x34) = 0;
    BGSSceneActionBase::Unk_0B();
}
