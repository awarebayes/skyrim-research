// BSBound declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-s-bsbound
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiExtraData.h for NiExtraData.
// BSBound: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSBound::LoadBinary, BSBound::CreateClone, BSBound::GetRTTI: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSBoundLoader, BSBoundLoader::Load, loaderA, loaderB: GUESS(low); names invented, Load is bound by address through bind-hints.json
// NiExtraData::LoadBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); bound by address through bind-hints.json
// NiRTTI_BSBound: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); bound by address through bind-hints.json
#pragma once

#include <cstdint>
#include <cstddef>
#include "../netimmerse/NiExtraData.h"

// NiRTTI_BSBound: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the RTTI object at RVA 0x332e3a0 that GetRTTI addresses, bound by hint
extern const NiRTTI NiRTTI_BSBound;

// BSBoundLoader: GUESS(low); embedded twice at 0x18 and 0x24, 0xC bytes each; Load is declared only and bound by address
class BSBoundLoader
{
public:
    void Load(NiStream& a_stream);

    std::uint8_t unk00[0x0C];  // 00
};
static_assert(sizeof(BSBoundLoader) == 0x0C, "BSBoundLoader size");

class BSBound : public NiExtraData
{
public:
    virtual void LoadBinary(NiStream& a_stream);  // compared: 0xff17c0
    virtual NiObject* CreateClone(NiCloningProcess& a_cloning);  // compared: 0xff1760
    virtual const NiRTTI* GetRTTI() const;  // compared: 0xff1b90

    // loaderA, loaderB: GUESS(low); the two embedded loaders the load pass calls, at 0x18 and 0x24
    BSBoundLoader loaderA;  // 18
    BSBoundLoader loaderB;  // 24
};
static_assert(sizeof(BSBound) == 0x30, "BSBound size");
