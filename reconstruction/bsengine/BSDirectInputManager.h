// Type declarations for the BSDirectInputManager translation unit (build sse-steam-1-7-104).
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Class name, method names and the member at 08 follow CharmedBaryon/CommonLibSSE-NG
// b93280e832f263dbef44e44cbe2936622a02f91a (MIT): include/RE/B/BSDirectInputManager.h.
// No NG code is copied. GUID, DIDEVICEOBJECTDATA, IDirectInput8A and IDirectInputDevice8A are
// minimal stand-ins; their vtable slots are the ones the compared code calls.
//
// BSDirectInputManager: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// CreateDeviceWithGUID GetDeviceState GetDeviceData ReleaseDevice diInterface: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// GUID DIDEVICEOBJECTDATA IDirectInput8A IDirectInputDevice8A: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// CreateDevice Acquire Unacquire Poll Release QueryInterface AddRef: GUESS(high); public DirectInput 8 method names for the called slots
// unk3 unk4 unk5 unk6 unk11 unk12 unk13 unk14 unk15 unk16 unk17 unk18 unk19 unk20 unk21 unk22 unk23 unk24: GUESS; slot fillers

#pragma once

#include <cstdint>

struct GUID {
    std::uint32_t data1;
    std::uint16_t data2;
    std::uint16_t data3;
    std::uint8_t  data4[8];
};

struct DIDEVICEOBJECTDATA {
    std::uint32_t  ofs;
    std::uint32_t  data;
    std::uint32_t  timeStamp;
    std::uint32_t  sequence;
    std::uintptr_t appData;
};

class IDirectInputDevice8A {
public:
    virtual std::int32_t QueryInterface();                    // slot 0
    virtual std::uint32_t AddRef();                           // slot 1
    virtual std::uint32_t Release();                          // slot 2
    virtual void unk3();
    virtual void unk4();
    virtual void unk5();
    virtual void unk6();
    virtual std::int32_t Acquire();                           // slot 7
    virtual std::int32_t Unacquire();                         // slot 8
    virtual std::int32_t GetDeviceState(std::uint32_t a_size, void* a_data);  // slot 9
    virtual std::int32_t GetDeviceData(std::uint32_t a_objectSize, DIDEVICEOBJECTDATA** a_data,
                                       std::uint32_t* a_count, std::uint32_t a_flags);  // slot 10
    virtual void unk11();
    virtual void unk12();
    virtual void unk13();
    virtual void unk14();
    virtual void unk15();
    virtual void unk16();
    virtual void unk17();
    virtual void unk18();
    virtual void unk19();
    virtual void unk20();
    virtual void unk21();
    virtual void unk22();
    virtual void unk23();
    virtual void unk24();
    virtual std::int32_t Poll();                              // slot 25
};

class IDirectInput8A {
public:
    virtual std::int32_t QueryInterface();                    // slot 0
    virtual std::uint32_t AddRef();                           // slot 1
    virtual std::uint32_t Release();                          // slot 2
    virtual std::int32_t CreateDevice(const GUID* a_guid, IDirectInputDevice8A** a_device,
                                      void* a_outer);         // slot 3
};

class BSDirectInputManager {
public:
    IDirectInputDevice8A* CreateDeviceWithGUID(GUID* a_guid);
    void GetDeviceState(IDirectInputDevice8A* a_device, std::uint32_t a_size, void* a_outData);
    void GetDeviceData(IDirectInputDevice8A* a_device, std::uint32_t* a_dataSize,
                       DIDEVICEOBJECTDATA** a_outData);
    void ReleaseDevice(IDirectInputDevice8A* a_device);

    std::uint32_t   pad00;        // 00
    IDirectInput8A* diInterface;  // 08
};
