// BGSFootstep::~BGSFootstep (deleting destructor), build sse-steam-1-7-104.
//
// Labels: v2
// Task: batch5-s08-tesform-bgsfootstep
// RVA 0x31cac0, 64 bytes (~BGSFootstep, the scalar deleting destructor in vftable slot 0);
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from the local instruction listing of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT) unless labelled in the header.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions listed above are compared.
#include "BGSFootstep.h"

// The constructor is not compared: it is defined so that this unit emits the vftable and with it
// the deleting destructor.
BGSFootstep::BGSFootstep()
{
}

// TestBit: GUESS(low); a flag-word bit test by bit index, taking the word by value.
inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}

// RVA 0x31c770, 65 bytes
// Near-miss: near-miss/0x31c770.cpp

// RVA 0x31ca20, 93 bytes
void BGSFootstep::InitItemImpl()
{
    if (!TestBit(formFlags, 3)) {
        std::uint32_t id = static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(impactSet));
        if (id != 0) {
            AddCompileIndex(id, GetFile(-1));
            TESForm* found = LookupByID(id);
            if (found && static_cast<std::uint8_t>(found->formType) == 'e') {
                impactSet = reinterpret_cast<BGSImpactDataSet*>(found);
            }
        }
        SetFormFlag(true);
    }
}

