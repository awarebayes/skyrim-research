// BSImagespaceShader declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bsimagespaceshader
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: local stand-ins (no ancestor has a shared header).
// BSImagespaceShader: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// NiRefObject, BSShader: STANDIN EXE_RTTI
// BSImagespaceShader::Unk_0D, BSImagespaceShader::RestoreRenderStates, BSImagespaceShader::UpdateParams, BSImagespaceShader::Unk_0C, BSImagespaceShader::ShutDown, BSImagespaceShader::Setup: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); Unk_0D and Unk_0C signatures derived from the listing
// ImageSpaceEffectParam, ImageSpaceManager: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSImagespaceShader::DispatchCopySubRegion: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// NiRefObject::~NiRefObject, unknown08, unknown10, unknown90: GUESS(low)
// Unk_07, Unk_08, Unk_09: GUESS(low); placeholders so the vtable slots that the listings call match their offsets
// Unk_0A, Unk_0B: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); placeholders for the slots the listings call
// m_slots, m_slotCount, m_renderState, m_statesDirty, ImageSpaceSlot, ImageSpaceRenderState, SetSlotIndex, ApplyRenderStates, ApplyShadowState, FinalizeCommit, ResetRenderStates: GUESS(low)
// SubRegionTarget, SubRegionTarget::Dispatch, CopySubRegionRequest, SubRegion, CopySubRegionToTarget: GUESS(low)
// Renderer, g_renderer, Renderer::SetFlagA, Renderer::SetFlagB, Renderer::SetFlagC, Renderer::SetFlagD, Renderer::SetFlagE, Renderer::SetFlagF, Renderer::CopyBytes: GUESS(low)
// g_shadowFlags, g_shadowModeA, g_shadowModeB, g_shadowSlotB, g_shadowDirtyB: GUESS(low); the globals are bound by the unit's bind-hints.json
#pragma once

#include <cstdint>
#include <cstddef>

class ImageSpaceEffectParam;
class ImageSpaceManager;
class ImageSpaceSlot;

class NiRefObject
{
public:
    virtual ~NiRefObject() = default;
    std::uint8_t unknown08[0x8];  // 08
};
static_assert(sizeof(NiRefObject) == 0x10, "NiRefObject size");

class BSShader : public NiRefObject
{
public:
    std::uint8_t unknown10[0x80];  // 10
};
static_assert(sizeof(BSShader) == 0x90, "BSShader size");

// Object held at BSImagespaceShader+0x198; slot 2 takes four values after the object.
class ImageSpaceRenderState
{
public:
    virtual ~ImageSpaceRenderState() = default;
    // Slot01: GUESS(low)
    virtual void Slot01();
    virtual void Apply(std::uint32_t a_mode, std::uint32_t a_x, std::uint32_t a_y, std::uint32_t a_z);
};

// Target object at the first qword of a CopySubRegionRequest; slot 12 dispatches compute work.
class SubRegionTarget
{
public:
    virtual ~SubRegionTarget() = default;
    // Slot01 through Slot11: GUESS(low); placeholders so Dispatch lands on slot 12
    virtual void Slot01();
    virtual void Slot02();
    virtual void Slot03();
    virtual void Slot04();
    virtual void Slot05();
    virtual void Slot06();
    virtual void Slot07();
    virtual void Slot08();
    virtual void Slot09();
    virtual void Slot10();
    virtual void Slot11();
    virtual void Dispatch(std::uint32_t a_groupsX, std::uint32_t a_groupsY, std::uint32_t a_groupsZ);
};

class Renderer
{
public:
    void SetFlagA(std::uint32_t a_index, std::uint64_t a_value);
    void SetFlagB(std::uint32_t a_index, std::uint64_t a_value);
    void SetFlagC(std::uint32_t a_index, std::uint32_t a_value);
    void SetFlagD(std::uint32_t a_index, std::uint32_t a_value);
    void SetFlagE(std::uint32_t a_index, std::uint32_t a_value);
    void SetFlagF(std::uint32_t a_index, std::uint32_t a_value);
    void CopyBytes(void* a_dst, std::uint32_t a_size);
};
extern Renderer g_renderer;

// Shadow-state globals read and written by ShutDown and Setup.
extern std::uint32_t g_shadowFlags;
extern std::uint32_t g_shadowModeA;
extern std::uint32_t g_shadowModeB;
extern std::uint32_t g_shadowSlotB;
extern bool g_shadowDirtyB;

void SetSlotIndex(ImageSpaceSlot* a_slot, std::uint32_t a_index);
bool ApplyRenderStates(ImageSpaceRenderState* a_state);
void ApplyShadowState();
void FinalizeCommit(bool a_flag);

class BSImagespaceShader : public BSShader
{
public:
    virtual std::uint64_t* Unk_0D(std::uint64_t* a_out);  // compared: 0x15651e0
    virtual bool RestoreRenderStates(ImageSpaceEffectParam* a_param);  // compared: 0x1564df0
    virtual void UpdateParams(ImageSpaceEffectParam* a_param);  // compared: 0x1564d90
    virtual void Unk_0C(std::uint32_t a_x, std::uint32_t a_y, std::uint32_t a_z);  // compared: 0x1565170
    virtual void ShutDown();  // compared: 0x1564a00
    virtual void Setup(ImageSpaceManager* a_manager, ImageSpaceEffectParam* a_param);  // compared: 0x1564960
    // Unk_07, Unk_08, Unk_09: GUESS(low); placeholders for vtable slots 7 to 9
    virtual void Unk_07();
    virtual void Unk_08();
    virtual void Unk_09();
    // Unk_0A, Unk_0B: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slots the listings call on this
    virtual void Unk_0A();
    virtual void Unk_0B();

    bool ResetRenderStates();

    // The first qword of the request is a target object, not a vtable, so this stays a static function.
    static std::uint32_t DispatchCopySubRegion(struct CopySubRegionRequest* a_request);  // compared: 0x1540db0

    std::uint8_t unknown90[0x48];  // 90
    // m_slots: GUESS(low)
    ImageSpaceSlot** m_slots;      // d8
    std::uint8_t unknownE0[0x98];  // e0
    // m_slotCount: GUESS(low)
    std::uint32_t m_slotCount;     // 178
    std::uint8_t unknown17C[0x1C];  // 17c
    // m_renderState: GUESS(low)
    ImageSpaceRenderState* m_renderState;  // 198
    std::uint8_t unknown1A0[0x1];  // 1a0
    // m_statesDirty: GUESS(low)
    bool m_statesDirty;            // 1a1
    std::uint8_t unknown1A2[0x6];  // 1a2
};
static_assert(sizeof(BSImagespaceShader) == 0x1A8, "BSImagespaceShader size");

// SubRegion: GUESS(low)
struct SubRegion
{
    std::uint32_t a;      // 00
    std::uint32_t b;      // 04
    std::uint32_t width;  // 08
    std::uint32_t height; // 0c
    std::uint8_t unknown10[0x10];  // 10
};
static_assert(sizeof(SubRegion) == 0x20, "SubRegion size");

// CopySubRegionRequest: GUESS(low)
struct CopySubRegionRequest
{
    SubRegionTarget* target;       // 00
    std::uint8_t unknown08[0x8];   // 08
    // value10, value18: GUESS(low)
    std::uint64_t value10;         // 10
    std::uint64_t value18;         // 18
    std::uint8_t unknown20[0x10];  // 20
    // value30, value34, value38, value3C: GUESS(low)
    std::uint32_t value30;         // 30
    std::uint32_t value34;         // 34
    std::uint32_t value38;         // 38
    std::uint32_t value3C;         // 3c
    SubRegion rect;                // 40
    // mode: GUESS(low)
    std::uint32_t mode;            // 60
};

void CopySubRegionToTarget(SubRegionTarget* a_target, const SubRegion* a_rect);
