// NiMultiTargetTransformController declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-nimultitargettransformcontroller
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../netimmerse/NiTimeController.h for NiTimeController.
// NiMultiTargetTransformController: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiInterpController: STANDIN EXE_RTTI
// NiMultiTargetTransformController::GetInterpolatorCount, NiMultiTargetTransformController::GetInterpolatorID, NiMultiTargetTransformController::~NiMultiTargetTransformController, NiMultiTargetTransformController::GuaranteeTimeRange, NiMultiTargetTransformController::GetInterpolatorIndex, NiMultiTargetTransformController::LoadBinary, NiMultiTargetTransformController::SaveBinary, NiMultiTargetTransformController::IsEqual, NiMultiTargetTransformController::ResetTimeExtrema, NiMultiTargetTransformController::ProcessClone: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// IsEqualEntry, ProcessCloneEntry, WriteRef, GetActiveTimeRange: GUESS(low); the entry and stream slots the listings call; the shared NiInterpolator header uses the first two names at slots 0x32 and 0x33
// Slot00..Slot1B, Slot1E..Slot31: GUESS(low); placeholders so the called slots land on their offsets
// Slot00..Slot0B: GUESS(low); placeholders so WriteRef lands on slot 12
// ControlledEntry, NiStreamBuffer, CloneNode, NiCloningProcess, NiStreamTransferFn, NiStream::inBuffer, NiStream::outBuffer: GUESS(low)
// NiMultiTargetTransformController::m_entries, NiMultiTargetTransformController::m_entryPtrs, NiMultiTargetTransformController::m_count: GUESS(low)
// AllocateEntries, LoadEntry, FinishTimeExtrema, HashPointer, NiTimeControllerLoadBinary, NiTimeControllerSaveBinary, NiTimeControllerIsEqual: GUESS(low); the callees the listings call
// ?__global_delete: GUESS(low); the global sized operator delete the deleting destructor calls
// g_missingInterpolatorIndex: GUESS(low); the default index the lookup returns on a miss, bound by the unit's bind-hints.json
// TimeFlags, ExtremaBegin, ExtremaEnd, TestBit: GUESS(low); accessors for the base's unnamed padding and bit test
#pragma once

#include <cstdint>
#include <cstddef>
#include "../netimmerse/NiTimeController.h"

class NiStream;
class NiStreamBuffer;
class ControlledEntry;
class NiInterpController;

// CloneNode: GUESS(low); one node of a clone table chain
struct CloneNode
{
    std::uint64_t key;    // 00
    std::uint64_t value;  // 08
    CloneNode* next;      // 10
};
static_assert(sizeof(CloneNode) == 0x18, "CloneNode size");

// NiCloningProcess: GUESS(low); only the clone table the compared code reads
class NiCloningProcess
{
public:
    std::uint8_t unknown00[0x0C];  // 00
    std::uint32_t bucketCount;     // 0c
    std::uint8_t unknown10[0x08];  // 10
    CloneNode* endNode;            // 18
    std::uint8_t unknown20[0x08];  // 20
    CloneNode* buckets;            // 28
};
static_assert(sizeof(NiCloningProcess) == 0x30, "NiCloningProcess size");

// ControlledEntry: GUESS(low); the 0x48-byte entries the controller drives
class ControlledEntry
{
public:
    // Slot00..Slot1B, Slot1E..Slot31: GUESS(low); placeholders so the called slots land on their offsets
    virtual void Slot00();
    virtual void Slot01();
    virtual void Slot02();
    virtual void Slot03();
    virtual void Slot04();
    virtual void Slot05();
    virtual void Slot06();
    virtual void Slot07();
    virtual void Slot08();
    virtual void Slot09();
    virtual void Slot0A();
    virtual void Slot0B();
    virtual void Slot0C();
    virtual void Slot0D();
    virtual void Slot0E();
    virtual void Slot0F();
    virtual void Slot10();
    virtual void Slot11();
    virtual void Slot12();
    virtual void Slot13();
    virtual void Slot14();
    virtual void Slot15();
    virtual void Slot16();
    virtual void Slot17();
    virtual void Slot18();
    virtual void Slot19();
    virtual void Slot1A();
    virtual void Slot1B();
    // IsEqualEntry: GUESS(low); slot 28 (0xE0), called with the entry alone
    virtual bool IsEqualEntry();
    // ProcessCloneEntry: GUESS(low); slot 29 (0xE8)
    virtual void ProcessCloneEntry(NiCloningProcess& a_cloning);
    virtual void Slot1E();
    virtual void Slot1F();
    virtual void Slot20();
    virtual void Slot21();
    virtual void Slot22();
    virtual void Slot23();
    virtual void Slot24();
    virtual void Slot25();
    virtual void Slot26();
    virtual void Slot27();
    virtual void Slot28();
    virtual void Slot29();
    virtual void Slot2A();
    virtual void Slot2B();
    virtual void Slot2C();
    virtual void Slot2D();
    virtual void Slot2E();
    virtual void Slot2F();
    virtual void Slot30();
    virtual void Slot31();
    // GetActiveTimeRange: GUESS(low); slot 50 (0x190)
    virtual void GetActiveTimeRange(float& a_begin, float& a_end) const;
    // GuaranteeTimeRange: GUESS(low); slot 51 (0x198)
    virtual void GuaranteeTimeRange(float a_start, float a_end);

    std::uint8_t unknown08[0x8];   // 08
    const char* name;              // 10
    std::uint8_t unknown18[0x30];  // 18
};
static_assert(sizeof(ControlledEntry) == 0x48, "ControlledEntry size");

// NiStreamBuffer: GUESS(low); a stream side whose transfers are plain function pointers, not virtuals
class NiStreamBuffer;
using NiStreamTransferFn = std::int32_t (*)(NiStreamBuffer* a_self, void* a_buf, std::uint32_t a_size, std::uint32_t* a_out, std::uint32_t a_count);
class NiStreamBuffer
{
public:
    std::uint8_t unknown00[0x8];   // 00
    std::int32_t transferred;      // 08
    // readFn, writeFn: GUESS(low); the transfer functions at +0x10 and +0x18
    NiStreamTransferFn readFn;     // 10
    NiStreamTransferFn writeFn;    // 18
};
static_assert(sizeof(NiStreamBuffer) == 0x20, "NiStreamBuffer size");

// NiStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the buffers and WriteRef are declared
class NiStream
{
public:
    // Slot00..Slot0B: GUESS(low); placeholders so WriteRef lands on slot 12
    virtual void Slot00();
    virtual void Slot01();
    virtual void Slot02();
    virtual void Slot03();
    virtual void Slot04();
    virtual void Slot05();
    virtual void Slot06();
    virtual void Slot07();
    virtual void Slot08();
    virtual void Slot09();
    virtual void Slot0A();
    virtual void Slot0B();
    // WriteRef: GUESS(low); slot 12 (0x60), called with an entry
    virtual void WriteRef(ControlledEntry* a_entry);

    std::uint8_t unknown08[0x290];  // 08
    // inBuffer, outBuffer: GUESS(low); the read side at +0x298 and the write side at +0x2A0
    NiStreamBuffer* inBuffer;   // 298
    NiStreamBuffer* outBuffer;  // 2a0
};

// AllocateEntries, LoadEntry, FinishTimeExtrema, HashPointer, NiTimeControllerLoadBinary, NiTimeControllerSaveBinary, NiTimeControllerIsEqual: GUESS(low)
ControlledEntry* LoadEntry(NiStream* a_stream);
void HashPointer(std::uint32_t* a_out, const void* a_ptr);
void NiTimeControllerLoadBinary(NiStream& a_stream);
void NiTimeControllerSaveBinary(NiStream& a_stream);
bool NiTimeControllerIsEqual(NiObject* a_object);

// g_missingInterpolatorIndex: GUESS(low)
extern std::uint16_t g_missingInterpolatorIndex;

// TestBit: GUESS(low); bit test on a flags word
inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit)
{
    return ((a_flags >> a_bit) & 1) != 0;
}

class NiInterpController : public NiTimeController
{
public:
};
static_assert(sizeof(NiInterpController) == 0x48, "NiInterpController size");

// TimeFlags, ExtremaBegin, ExtremaEnd: GUESS(low); NiTimeController keeps these in its unnamed unk10 padding, so they are read in place
inline std::uint8_t TimeFlags(NiInterpController* a_self)
{
    return *(reinterpret_cast<std::uint8_t*>(a_self) + 0x10);
}
inline float& ExtremaBegin(NiInterpController* a_self)
{
    return *reinterpret_cast<float*>(reinterpret_cast<std::uint8_t*>(a_self) + 0x1C);
}
inline float& ExtremaEnd(NiInterpController* a_self)
{
    return *reinterpret_cast<float*>(reinterpret_cast<std::uint8_t*>(a_self) + 0x20);
}

// FinishTimeExtrema: GUESS(low); the callee ResetTimeExtrema ends with when the extrema are unset
void FinishTimeExtrema(NiInterpController* a_self);

class NiMultiTargetTransformController : public NiInterpController
{
public:
    NiMultiTargetTransformController();
    virtual std::uint16_t GetInterpolatorCount() const;  // compared: 0xf5de10
    virtual const char* GetInterpolatorID(std::uint16_t a_index = 0);  // compared: 0xf5de20
    virtual ~NiMultiTargetTransformController();  // compared: 0xf5b520 (scalar deleting destructor)
    virtual void GuaranteeTimeRange(float a_startTime, float a_endTime);  // compared: 0xf5e280
    virtual std::uint16_t GetInterpolatorIndex(const char* a_id) const;  // compared: 0xf5de40
    virtual void LoadBinary(NiStream& a_stream);  // compared: 0xf5d7a0
    virtual void SaveBinary(NiStream& a_stream);  // compared: 0xf5d860
    virtual bool IsEqual(NiObject* a_object);  // compared: 0xf5d900
    virtual void ResetTimeExtrema();  // compared: 0xf5df30
    virtual void ProcessClone(NiCloningProcess& a_cloning);  // compared: 0xf5e350

    // AllocateEntries: GUESS(low); the callee that sizes the entry arrays
    void AllocateEntries(std::uint16_t a_count);

    // m_entries: GUESS(low); inline entries, stride 0x48
    ControlledEntry* m_entries;  // 48
    // m_entryPtrs: GUESS(low); one pointer per entry
    ControlledEntry** m_entryPtrs;  // 50
    // m_count: GUESS(low)
    std::uint16_t m_count;  // 58
    std::uint8_t unknown5A[0x6];  // 5a
};
static_assert(sizeof(NiMultiTargetTransformController) == 0x60, "NiMultiTargetTransformController size");
