// Type declarations for the NiTimeController translation unit (build sse-steam-1-7-104).
//
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names follow CharmedBaryon/CommonLibSSE-NG b93280e832f263dbef44e44cbe2936622a02f91a (MIT):
// include/RE/N/NiObject.h, include/RE/N/NiTimeController.h. No NG code is copied; these are
// minimal stand-ins reproducing only the layout the reconstructed function depends on.
// COMMUNITY: NiObject, NiTimeController, ProcessClone (slot 0x1D), NiCloningProcess, next (0x40).
// GUESS: unk01..unk1C are unnamed vftable slots kept only to place ProcessClone at slot 0x1D;
//        the vftable pointer, reference count and padding up to 0x40 are layout only.
#pragma once

#include <cstdint>

class NiCloningProcess;

class NiObject {
public:
    virtual ~NiObject();
    virtual void unk01();
    virtual void unk02();
    virtual void unk03();
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
    virtual void unk1A();
    virtual void unk1B();
    virtual void unk1C();
    virtual void ProcessClone(NiCloningProcess& a_cloning);  // 1D

    std::int32_t refCount;  // 0x08
};

class NiTimeController : public NiObject {
public:
    void ProcessClone(NiCloningProcess& a_cloning) override;  // 1D

    std::uint8_t      unk10[0x30];  // 0x10
    NiTimeController* next;         // 0x40
};
