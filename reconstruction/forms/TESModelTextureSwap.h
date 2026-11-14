// TESModelTextureSwap type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and slot order follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESModelTextureSwap.h
// and the vftables of the pinned image. BaseFormComponent and TESModel are stand-ins, labelled where
// they are declared; only class names, base chain, slot
// order and sizes are claimed, slot signatures other than the compared ones are placeholders.
// TESModelTextureSwap: EXE_RTTI; class name and base from the image RTTI
#pragma once

#include <cstdint>

// BaseFormComponent: STANDIN EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
// sizeof BaseFormComponent 0x8: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class BaseFormComponent
{
public:
	// BaseFormComponent::~BaseFormComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
	virtual ~BaseFormComponent();  // 00
	// BaseFormComponent::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1
	virtual void InitializeDataComponent();  // 01
	// BaseFormComponent::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2
	virtual void ClearDataComponent();  // 02
	// BaseFormComponent::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3
	virtual void CopyComponent();  // 03
};
static_assert(sizeof(BaseFormComponent) == 0x8, "layout");

// TESModel: STANDIN EXE_RTTI; class name and base from the image RTTI, 7 primary vftable slots
class TESModel : public BaseFormComponent
{
public:
	// TESModel::~TESModel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
	~TESModel() override;  // 00
	// TESModel::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1
	void InitializeDataComponent() override;  // 01
	// TESModel::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2
	void ClearDataComponent() override;  // 02
	// TESModel::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3
	void CopyComponent() override;  // 03
	// TESModel::GetModel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 4
	virtual void GetModel();  // 04
	// TESModel::SetModel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 5
	virtual void SetModel();  // 05
	// TESModel::GetAsModelTextureSwap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 6
	virtual void GetAsModelTextureSwap();  // 06

	// unk08: GUESS(low); members not recovered yet, sized so the static_assert holds
	std::uint8_t unk08[0x20];  // 08
};
static_assert(sizeof(TESModel) == 0x28, "layout");

// TESModelTextureSwap: EXE_RTTI; class name and base from the image RTTI
class TESModelTextureSwap : public TESModel
{
public:
	// TESModelTextureSwap::~TESModelTextureSwap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
	~TESModelTextureSwap() override;  // 00
	// TESModelTextureSwap::InitializeDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1
	void InitializeDataComponent() override;  // 01
	// TESModelTextureSwap::ClearDataComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 2
	void ClearDataComponent() override;  // 02
	// TESModelTextureSwap::CopyComponent: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 3
	void CopyComponent() override;  // 03
	// TESModelTextureSwap::GetAsModelTextureSwap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 6
	void GetAsModelTextureSwap() override;  // 06
	// ReleaseAlternateTextures: GUESS(low); the helper the target calls first in ClearDataComponent, takes this in RCX
	void ReleaseAlternateTextures();

	// alternateTextures: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares AlternateTexture*, an opaque pointer here
	void* alternateTextures;  // 28
	// numAlternateTextures: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint32_t numAlternateTextures;  // 30
	// pad34: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint32_t pad34;  // 34
};
static_assert(sizeof(TESModelTextureSwap) == 0x38, "layout");
