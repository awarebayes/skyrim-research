// BGSMaterialObject type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT). TESForm comes from
// the shared header; only the members and slots the compared code needs are declared here.
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its
// threshold at the pinned checkouts.
// BGSMaterialObject, BGSMaterialObject::EnsureLoaded, BGSMaterialObject::fileData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSMaterialObject::fileData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares BSTArray<FILE_DATA>, here the stand-in BSTArray
// BSMaterialObject, BSMaterialObject::EnsureLoaded, ::~BSMaterialObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); size 0x58, two dword members read by EnsureLoaded
// BSMaterialObject::properties: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares BSTArray<NiPointer<NiProperty>>, here a pointer-less stand-in array
// BSMaterialObject::directionalData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; opaque bytes (offset 0x08 to 0x40)
// BSTArray, BSTArray::empty, ::size, ::_size: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; layout data, capacity, size read from the listing, element type not modelled
// BSTArray::_data, ::_capacity, ::pad0C, ::pad14: GUESS(low); the allocator pointer, capacity and padding
// TESModel: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG slots 04 to 06 (GetModel, SetModel, GetAsModelTextureSwap) as placeholders; size 0x28
// TESModel::modelData: GUESS(low); filler bytes for model, textures, addons and counts
// BGSMaterialObject::LoadFileData: GUESS(low); bound by hint to 0x321760, the target the listing reaches after adjusting this by -0x48
// BGSMaterialObject::BGSMaterialObject: GUESS(low); the implicit constructor, defined only so the unit emits the vftables and with them the destructor thunk
#pragma once

#include <cstdint>

#include "TESForm.h"

class TESModel : public BaseFormComponent {
public:
    ~TESModel() override;                                    // 00
    void InitializeDataComponent() override;                 // 01
    void ClearDataComponent() override;                      // 02
    void CopyComponent(BaseFormComponent* a_rhs) override;   // 03
    virtual const char* GetModel() const;                    // 04
    virtual void        SetModel(const char* a_model);       // 05
    virtual void*       GetAsModelTextureSwap();             // 06

    std::uint8_t modelData[0x20];  // 08
};
static_assert(sizeof(TESModel) == 0x28, "layout");

struct BSTArray {
    bool          empty() const { return _size == 0; }
    std::uint32_t size() const { return _size; }

    void*         _data;      // 00
    std::uint32_t _capacity;  // 08
    std::uint32_t pad0C;      // 0C
    std::uint32_t _size;      // 10
    std::uint32_t pad14;      // 14
};
static_assert(sizeof(BSTArray) == 0x18, "layout");

class BSMaterialObject {
public:
    virtual ~BSMaterialObject();  // 00
    virtual void EnsureLoaded();  // 01

    std::uint8_t directionalData[0x38];  // 08
    BSTArray     properties;             // 40
};
static_assert(sizeof(BSMaterialObject) == 0x58, "layout");

class BGSMaterialObject :
    public TESForm,           // 00
    public TESModel,          // 20
    public BSMaterialObject   // 48
{
public:
    BGSMaterialObject();
    ~BGSMaterialObject() override;  // 00

    void EnsureLoaded() override;  // BSMaterialObject 01

    void LoadFileData();

    BSTArray fileData;  // A0
};
static_assert(sizeof(BGSMaterialObject) == 0xB8, "layout");
