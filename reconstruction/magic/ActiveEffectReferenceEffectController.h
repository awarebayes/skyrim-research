// ActiveEffectReferenceEffectController declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-c2-s11-referenceeffectcontroll-activeef-419a131a48fa
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// ActiveEffectReferenceEffectController: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// ReferenceEffectController: STANDIN EXE_RTTI
// ActiveEffectReferenceEffectController::GetElapsedTime, ActiveEffectReferenceEffectController::GetNoInitialFlare, ActiveEffectReferenceEffectController::GetSourcePosition, ActiveEffectReferenceEffectController::GetEffectPersists, ActiveEffectReferenceEffectController::GetGoryVisuals, ActiveEffectReferenceEffectController::GetHitEffectShader, ActiveEffectReferenceEffectController::GetHitEffectArt: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiPoint3, TESEffectShader, BGSArtObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiPoint3: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); three floats only
// ActiveEffectReferenceEffectController::SetTarget: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// ReferenceEffectController::~ReferenceEffectController, unknown08: GUESS(low)
// ActiveEffectOwner, ActiveEffectSourceNode, ReferenceEffectRefData, ReferenceTarget: GUESS(low)
// ActiveEffectOwner::source, ActiveEffectOwner::elapsed, ActiveEffectOwner::flags, ReferenceEffectRefData::flags, ReferenceTarget::flags: GUESS(low)
// ActiveEffectSourceNode::position: GUESS(low)
// ActiveEffectReferenceEffectController::owner, ActiveEffectReferenceEffectController::targetHandle: GUESS(low)
// GetEffectRefData, GetEffectArtForRef, GetEffectShaderForRef: GUESS(low)
// TestBit: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class TESEffectShader;
class BGSArtObject;

class NiPoint3
{
public:
    float x;
    float y;
    float z;
};
static_assert(sizeof(NiPoint3) == 0xC, "NiPoint3 size");

class ReferenceEffectController
{
public:
    virtual ~ReferenceEffectController() = default;
};
static_assert(sizeof(ReferenceEffectController) == 0x8, "ReferenceEffectController size");

// Object at owner+0x38 in the controller's owner; GetSourcePosition returns a reference into it.
class ActiveEffectSourceNode
{
public:
    std::uint8_t unknown00[0xA0];
    NiPoint3 position;  // 0xA0
};
static_assert(offsetof(ActiveEffectSourceNode, position) == 0xA0, "ActiveEffectSourceNode::position offset");

// The object at controller+0x08.
class ActiveEffectOwner
{
public:
    std::uint8_t unknown00[0x38];
    ActiveEffectSourceNode* source;  // 0x38
    std::uint8_t unknown40[0x30];
    float elapsed;  // 0x70
    std::uint8_t unknown74[0x8];
    std::uint32_t flags;  // 0x7C
};
static_assert(offsetof(ActiveEffectOwner, elapsed) == 0x70, "ActiveEffectOwner::elapsed offset");
static_assert(offsetof(ActiveEffectOwner, flags) == 0x7C, "ActiveEffectOwner::flags offset");

// The object returned by GetEffectRefData.
class ReferenceEffectRefData
{
public:
    std::uint8_t unknown00[0x68];
    std::uint32_t flags;  // 0x68
};
static_assert(offsetof(ReferenceEffectRefData, flags) == 0x68, "ReferenceEffectRefData::flags offset");

// The object SetTarget receives; only its flags word is read.
class ReferenceTarget
{
public:
    std::uint8_t unknown00[0x28];
    std::uint32_t flags;  // 0x28
};
static_assert(offsetof(ReferenceTarget, flags) == 0x28, "ReferenceTarget::flags offset");

class TESEffectShader;

class ActiveEffectReferenceEffectController : public ReferenceEffectController
{
public:
    virtual float GetElapsedTime();  // compared: 0x5dc6d0
    virtual bool GetNoInitialFlare();  // compared: 0x5dc7f0
    virtual const NiPoint3& GetSourcePosition();  // compared: 0x5dc760
    virtual bool GetEffectPersists();  // compared: 0x5dc810
    virtual bool GetGoryVisuals();  // compared: 0x5dc830
    virtual TESEffectShader* GetHitEffectShader();  // compared: 0x5dc990
    virtual BGSArtObject* GetHitEffectArt();  // compared: 0x5dc950
    void SetTarget(ReferenceTarget* a_target);  // compared: 0x5dc660

    ActiveEffectOwner* owner;  // 0x08
    std::uint32_t targetHandle;  // 0x10
    std::uint8_t unknown14[0xC];  // 0x14
};
static_assert(sizeof(ActiveEffectReferenceEffectController) == 0x20, "ActiveEffectReferenceEffectController size");

// Declared, not defined: the target calls these, and attempt binds them by hint.
ReferenceEffectRefData* GetEffectRefData(ActiveEffectOwner* a_owner);
BGSArtObject* GetEffectArtForRef(ReferenceEffectRefData* a_ref, bool a_flag);
TESEffectShader* GetEffectShaderForRef(ReferenceEffectRefData* a_ref, bool a_flag);
void CreateRefHandle(std::uint32_t* a_out, ReferenceTarget* a_target);
// RefHandleStandIn: GUESS(low); eight-byte stand-in for the handle slot
extern std::uint32_t gNullHandle;

inline bool TestBit(std::uint32_t a_flags, std::uint32_t a_bit) { return ((a_flags >> a_bit) & 1) != 0; }
