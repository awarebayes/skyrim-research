// Type declarations for the NiPSysModifier translation unit (build sse-steam-1-7-104).
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/N/NiPSysModifier.h,
// NiObject.h, NiStream.h, NiBinaryStream.h, NiCloningProcess.h. Vtable order and class size come
// from the image RTTI and vftable (class skeleton).
// Adapted code: the NiBinaryStream ReadFn and WriteFn aliases and the read, write and put
// template bodies are adapted from NG b93280e include/RE/N/NiBinaryStream.h and
// src/RE/N/NiBinaryStream.cpp under its MIT licence: put is NG's body; read and write fold in
// NG's binary_read and binary_write and return true instead of comparing the byte count.
// The bodies of LinkObject, RegisterStreamables and ProcessClone in NiPSysModifier.cpp closely
// parallel the same methods in momusdigital/fnv_decomp 91e1b6e8 (no licence; used by maintainer
// decision, docs/authorizations.md); the Sibling source lines there name the files. Bodies
// adapted from community sources are listed above; tools/check_origin.py reports none other
// above its threshold (0.75) at CommonLibSSE-NG b93280e, powerof3/CommonLibSSE 654e55f and
// momusdigital/fnv_decomp 91e1b6e8. NG's licence notice, from its LICENSE at b93280e, is kept as
// it requires:
//
//   MIT License
//
//   Copyright (c) 2018 Ryan-rsm-McKenzie
//
//   Permission is hereby granted, free of charge, to any person obtaining a copy
//   of this software and associated documentation files (the "Software"), to deal
//   in the Software without restriction, including without limitation the rights
//   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//   copies of the Software, and to permit persons to whom the Software is
//   furnished to do so, subject to the following conditions:
//
//   The above copyright notice and this permission notice shall be included in all
//   copies or substantial portions of the Software.
//
//   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
//   SOFTWARE.
//
// NiRefObject, NiObject: STANDIN EXE_RTTI COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slots only, 0x10 bytes
// NiPSysModifier: EXE_RTTI COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; 0x30 bytes, size from the listings
// NiStream, NiBinaryStream, NiCloningProcess, BSFixedString, NiParticleSystem, NiPSysData, NiPoint3, NiColorA: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the members and slots the unit uses
// CRC32Calculator: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only SizeOf64
#pragma once

#include <cstdint>

class NiPSysData;
class NiPoint3;
class NiColorA;
class NiParticleSystem;
class NiStream;
class NiCloningProcess;

// BSFixedString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); an interned string, compared by pointer
// data: GUESS(low); NG hides the pointer behind a getter
class BSFixedString {
public:
    bool operator==(const BSFixedString& a_rhs) const { return data == a_rhs.data; }

    const char* data;
};

// CRC32Calculator::SizeOf64: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); hash of a 64-bit key
class CRC32Calculator {
public:
    static void SizeOf64(std::uint32_t& a_crc, std::uint64_t a_data);
};

// NiBinaryStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// _absoluteCurrentPos, _readFn, _writeFn: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// read, write, put: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); bodies inlined as the image does
class NiBinaryStream {
public:
    using ReadFn = std::uint32_t(NiBinaryStream*, void*, std::uint32_t, std::uint32_t*, std::uint32_t);
    using WriteFn = std::uint32_t(NiBinaryStream*, const void*, std::uint32_t, std::uint32_t*, std::uint32_t);

    template <class CharT>
    bool read(CharT* a_str, std::uint32_t a_count)
    {
        std::uint32_t size = sizeof(CharT);
        std::uint32_t toRead = a_count * size;
        _absoluteCurrentPos += _readFn(this, a_str, toRead, &size, 1);
        return true;
    }

    template <class CharT>
    bool write(const CharT* a_str, std::uint32_t a_count)
    {
        std::uint32_t size = sizeof(CharT);
        std::uint32_t toWrite = a_count * size;
        _absoluteCurrentPos += _writeFn(this, a_str, toWrite, &size, 1);
        return true;
    }

    template <class CharT>
    bool put(CharT a_ch)
    {
        return write(&a_ch, 1);
    }

    virtual ~NiBinaryStream();

    std::uint32_t _absoluteCurrentPos;  // 08
    std::uint32_t _pad0C;               // 0C
    ReadFn*       _readFn;              // 10
    WriteFn*      _writeFn;             // 18
};

// NiStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// RegisterFixedString, SaveLinkID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slots 08 and 0C
// unk01..unk07: GUESS(low); slots kept only to place the named ones
// nifMaxVersion, iStr, oStr: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unk08, unk104: GUESS(low); layout filler between the observed members
// LoadFixedString, LoadFixedStringLegacy, SaveFixedString, LoadLinkID, ReadLinkID: GUESS; non-virtual callees, bound by hint
class NiAVObject;

class NiStream {
public:
    virtual ~NiStream();
    virtual void unk01();
    virtual void unk02();
    virtual void unk03();
    virtual void unk04();
    virtual void unk05();
    virtual void unk06();
    virtual void unk07();
    virtual bool RegisterFixedString(const BSFixedString& a_fixedString);  // 08
    virtual void unk09();
    virtual void unk0A();
    virtual void unk0B();
    virtual void SaveLinkID(const class NiObject* a_object);  // 0C

    void LoadFixedString(BSFixedString& a_string);
    void LoadFixedStringLegacy(BSFixedString& a_string);
    void SaveFixedString(const BSFixedString& a_string);
    void LoadLinkID();
    NiAVObject* ReadLinkID();

    std::uint8_t   unk08[0xF8];   // 08
    std::uint32_t  nifMaxVersion; // 100
    std::uint8_t   unk104[0x194]; // 104
    NiBinaryStream* iStr;         // 298
    NiBinaryStream* oStr;         // 2A0
};

// NiCloningProcess: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the clone map's table fields
// cloneMap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); BSTHashMap<NiObject*, NiObject*>
// CloneMapEntry, CloneMap, find: GUESS(low); the scatter-table chain walk spelled out because
//   the NG BSTHashMap template is not reproduced; layout read from the image
// BSTScatterTable::_capacity, BSTScatterTable::_sentinel, BSTScatterTableHeapAllocator::_entries: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG's scatter-table member names at NG's offsets, used for the same fields of CloneMap (_entries is the allocator's, at 0x08 of the allocator at 0x20)
// unk00, unk10, unk20: GUESS(low); placeholders for NG's _pad00/_pad08, _free/_good and the allocator's first word, unused here
class NiObject;

struct CloneMapEntry {
    NiObject*      first;   // 00
    NiObject*      second;  // 08
    CloneMapEntry* next;    // 10
};

struct CloneMap {
    // hot path: the engine inlines the hash lookup at each use
    // find writes a_out only on a hit, as the image's lookup leaves the caller's value untouched
    __forceinline bool find(NiObject* a_key, NiObject*& a_out) const
    {
        std::uint32_t hash;
        CRC32Calculator::SizeOf64(hash, reinterpret_cast<std::uint64_t>(a_key));
        if (!_entries) {
            return false;
        }
        CloneMapEntry* entry = &_entries[(_capacity - 1) & hash];
        if (!entry->next) {
            return false;
        }
        do {
            if (entry->first == a_key) {
                a_out = entry->second;
                return true;
            }
            entry = entry->next;
        } while (entry != _sentinel);
        return false;
    }

    std::uint8_t   unk00[0xC];  // 00
    std::uint32_t  _capacity;   // 0C
    std::uint8_t   unk10[0x8];  // 10
    CloneMapEntry* _sentinel;   // 18
    std::uint8_t   unk20[0x8];  // 20
    CloneMapEntry* _entries;    // 28
};

class NiCloningProcess {
public:
    CloneMap cloneMap;  // 00
};

// NiRefObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// unk08: GUESS(low); members not recovered
class NiRefObject {
public:
    virtual ~NiRefObject();
    virtual void DeleteThis();  // 01

    std::uint8_t unk08[0x8];  // 08
};

// NiObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// unk03..unk16, unk1E..unk24: GUESS(low); slots kept only to place the named ones
// GetRTTI, CreateClone, LoadBinary, LinkObject, RegisterStreamables, SaveBinary, IsEqual, ProcessClone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiObject : public NiRefObject {
public:
    ~NiObject() override;
    virtual void GetRTTI();  // 02
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
    virtual void CreateClone();                              // 17
    virtual void LoadBinary(NiStream& a_stream);             // 18
    virtual void LinkObject(NiStream& a_stream);             // 19
    virtual bool RegisterStreamables(NiStream& a_stream);    // 1A
    virtual void SaveBinary(NiStream& a_stream);             // 1B
    virtual bool IsEqual(NiObject* a_object);                // 1C
    virtual void ProcessClone(NiCloningProcess& a_cloning);  // 1D
    virtual void unk1E();
    virtual void unk1F();
    virtual void unk20();
    virtual void unk21();
    virtual void unk22();
    virtual void unk23();
    virtual void unk24();
};

// ORDER: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG wraps it in stl::enumeration<ORDER, std::uint32_t>
enum class ORDER : std::uint32_t {
    kKillOldParticles = 0,
    kBSLOD = 1,
    kEmitter = 1000,
    kSpawn = 2000,
    kGeneral = 3000,
    kForce = 4000,
    kCollider = 5000,
    kPosUpdate = 6000,
    kPostPosUpdate = 6500,
    kBoundUpdate = 7000,
    kBSStripUpdate = 8000
};

// name, order, target, active: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); order is a plain enum here, NG declares stl::enumeration
// pad1C, pad29: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); padding to 0x30; NG splits the tail into pad29, pad2A and pad2C, merged here into one 7-byte array
// Update, Initialize, HandleReset, SetActive, SetSystemPointer: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NiPSysModifier virtuals, slots 25 to 29
class NiPSysModifier : public NiObject {
public:
    ~NiPSysModifier() override;
    void GetRTTI() override;                            // 02
    void LoadBinary(NiStream& a_stream) override;       // 18
    void LinkObject(NiStream& a_stream) override;       // 19
    bool RegisterStreamables(NiStream& a_stream) override;  // 1A
    void SaveBinary(NiStream& a_stream) override;       // 1B
    bool IsEqual(NiObject* a_object) override;          // 1C
    void ProcessClone(NiCloningProcess& a_cloning) override;  // 1D

    virtual bool Update(float a_time, NiPSysData* a_particleData, NiPoint3* a_position, NiPoint3* a_radii, NiColorA* a_rotation) = 0;  // 25
    virtual void Initialize(NiPSysData* a_particleData, std::uint16_t, NiPoint3*);  // 26
    virtual void HandleReset();                                                      // 27
    virtual void SetActive(bool a_active);                                           // 28
    virtual void SetSystemPointer(NiParticleSystem* a_target);                       // 29

    BSFixedString     name;      // 10
    ORDER             order;     // 18
    std::uint32_t     pad1C;     // 1C
    NiParticleSystem* target;    // 20
    bool              active;    // 28
    std::uint8_t      pad29[7];  // 29
};
static_assert(sizeof(NiPSysModifier) == 0x30, "size from the deleting destructor");
