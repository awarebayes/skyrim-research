// BSProceduralLightningController declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bsprocedurallightningcontroller
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiTimeController.h for NiTimeController.
// NiInterpolator.h is not included: its NiObject is a different class from the one in
// NiTimeController.h, so both cannot be in one translation unit (header-gap NiInterpolator).
// BSProceduralLightningController: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// NiInterpController: STANDIN EXE_RTTI
// BSProceduralLightningController::GetInterpolator, BSProceduralLightningController::GetInterpolatorID, BSProceduralLightningController::TargetIsRequiredType, BSProceduralLightningController::LoadBinary, BSProceduralLightningController::InterpolatorIsCorrectType, BSProceduralLightningController::RegisterStreamables, BSProceduralLightningController::IsEqual: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// NiInterpolator, NiStream, NiRTTI: STANDIN COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../netimmerse/NiTimeController.h"

class NiInterpolator;
class NiStream;

// NiRTTI: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiRTTI
{
public:
    // name: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
    const char* name;
    // parent: OBSERVED
    const NiRTTI* parent;
};

// NiInterpolator: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Only the vtable slots the compared code calls are named: slot 0x10 is GetRTTI, slot 0x18 is the
// query made on the object at +0x38, slot 0xD0 is RegisterStreamables and slot 0xE0 is IsEqual.
class NiInterpolator
{
public:
    // unk00, unk01: GUESS(low)
    virtual void unk00();
    virtual void unk01();
    // GetRTTI: OBSERVED
    virtual const NiRTTI* GetRTTI() const;
    // unk03: OBSERVED
    virtual void* unk03();
    // unk04 through unk19: GUESS(low)
    virtual void unk04();
    virtual void unk05();
    virtual void unk06();
    virtual void unk07();
    virtual void unk08();
    virtual void unk09();
    virtual void unk0A();
    virtual void unk0B();
    virtual void unk0C();
    virtual void unk0D();
    virtual void unk0E();
    virtual void unk0F();
    virtual void unk10();
    virtual void unk11();
    virtual void unk12();
    virtual void unk13();
    virtual void unk14();
    virtual void unk15();
    virtual void unk16();
    virtual void unk17();
    virtual void unk18();
    virtual void unk19();
    // RegisterStreamables: OBSERVED
    virtual bool RegisterStreamables(NiStream& a_stream);
    // unk1B: GUESS(low)
    virtual void unk1B();
    // IsEqual: OBSERVED
    virtual bool IsEqual(NiInterpolator* a_object);
};

// Helpers the compared code calls directly. Each takes the object pointer as its first argument,
// as the member call does.
// NiTimeController_LoadBinary, NiTimeController_RegisterStreamables, NiTimeController_IsEqual: GUESS(low); enclosing NiTimeController::LoadBinary, RegisterStreamables and IsEqual in CharmedBaryon/CommonLibSSE-NG@b93280e (MIT)
void NiTimeController_LoadBinary(NiTimeController* a_self, NiStream& a_stream);
bool NiTimeController_RegisterStreamables(NiTimeController* a_self, NiStream& a_stream);
bool NiTimeController_IsEqual(NiTimeController* a_self, NiObject* a_object);
// StreamReadSlot, ReadStreamSubA, ReadStreamSubB, CompareSubA, CompareSubB: GUESS(low)
void StreamReadSlot(NiStream& a_stream);
void ReadStreamSubA(void* a_sub, NiStream& a_stream);
void ReadStreamSubB(void* a_sub, NiStream& a_stream);
bool CompareSubA(void* a_sub, void* a_other);
bool CompareSubB(void* a_sub, void* a_other);

// Image data: the RTTI objects and the ID name table.
// NiRTTI_NiFloatInterpolator, NiRTTI_NiBoolTimelineInterpolator: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
extern NiRTTI NiRTTI_NiFloatInterpolator;
extern NiRTTI NiRTTI_NiBoolTimelineInterpolator;
// g_procLightningIDNames: GUESS(low)
extern const char* const g_procLightningIDNames[9];

class NiInterpController : public NiTimeController
{
public:
};
static_assert(sizeof(NiInterpController) == 0x48, "NiInterpController size");

class BSProceduralLightningController : public NiInterpController
{
public:
    // GetInterpolatorCount: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
    virtual std::uint32_t GetInterpolatorCount() const;
    // GetInterpolator: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); RVA 0xffd880
    virtual NiInterpolator* GetInterpolator(std::uint16_t a_index = 0) const;
    // GetInterpolatorID: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); RVA 0xffd7d0
    virtual const char* GetInterpolatorID(std::uint16_t a_index = 0);
    // TargetIsRequiredType: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); RVA 0xffd790
    virtual bool TargetIsRequiredType() const;
    // LoadBinary: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); RVA 0xffc810
    virtual void LoadBinary(NiStream& a_stream);
    // InterpolatorIsCorrectType: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); RVA 0xffe540
    virtual bool InterpolatorIsCorrectType(NiInterpolator* a_interpolator, std::uint16_t a_index) const;
    // RegisterStreamables: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); RVA 0xffc920
    virtual bool RegisterStreamables(NiStream& a_stream);
    // IsEqual: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); RVA 0xffca50
    virtual bool IsEqual(NiObject* a_object);

    // unknown48: GUESS(low); padding up to the first member, apart from the offsets the bodies read
    std::uint8_t unknown48[0xB8];
    // object100: GUESS(low)
    NiInterpolator* object100;
    // interpolators: GUESS(low); nine entries read by index and compared one by one
    NiInterpolator* interpolators[9];
    // subA: GUESS(low); sub-object passed by address
    std::uint8_t subA[0x8];
    // subB: GUESS(low); sub-object passed by address
    std::uint8_t subB[0x38];
};
static_assert(sizeof(BSProceduralLightningController) == 0x190, "BSProceduralLightningController size");
