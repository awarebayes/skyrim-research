// BSLightingShaderMaterialSnow declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s10-bslightingshadermaterialsnow
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: unit-local stand-ins for BSShaderMaterial and BSLightingShaderMaterialBase.
// Header gap: the shared base omits its constructor; this unit declares it out of line
// so ordinary derived construction initializes the base once. Base fields are opaque here.
// BSLightingShaderMaterialSnow: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSLightingShaderMaterialSnow::GetFeature, BSLightingShaderMaterialSnow::CopyMembers, BSLightingShaderMaterialSnow::Ctor, BSLightingShaderMaterialSnow::ComputeCRC32: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unknownA0: GUESS(low)
// Stand-in declarations follow the shared header and CommonLibSSE-NG b93280e (MIT).
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
#pragma once

#include <cstdint>
// NiStream, BSTextureSet: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); declarations only
class NiStream;
class BSTextureSet;

// BSShaderMaterial: STANDIN EXE_RTTI; class name and base from the image RTTI, 8 primary vftable slots
// BSShaderMaterial::Feature, BSShaderMaterial::Type: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// sizeof BSShaderMaterial 0x38: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
// _refCount: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); member of NG's base BSIntrusiveRefCounted, declared here directly
// unk0C: GUESS(low); members not recovered yet, sized so the static_assert holds
// kDefault, kBase, kEffect, kLighting, kWater: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); Feature lists only its first enumerator here
// Create, CopyMembers, DoIsCopy, ComputeCRC32, GetDefault, GetFeature, GetType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); BSShaderMaterial virtuals, slots 01 to 07
class BSShaderMaterial
{
public:
	enum class Feature
	{
		kDefault = 0,
	};

	enum class Type
	{
		kBase = 0,
		kEffect = 1,
		kLighting = 2,
		kWater = 3
	};

	virtual ~BSShaderMaterial();  // 00
	virtual BSShaderMaterial* Create();  // 01
	virtual void CopyMembers(BSShaderMaterial* a_other);  // 02
	virtual bool DoIsCopy(BSShaderMaterial* a_other);  // 03
	virtual std::uint32_t ComputeCRC32();  // 04
	virtual BSShaderMaterial* GetDefault();  // 05
	virtual Feature GetFeature() const;  // 06
	virtual Type GetType() const;  // 07

	volatile std::uint32_t _refCount;  // 08
	std::uint8_t           unk0C[0x2C];  // 0C
};
static_assert(sizeof(BSShaderMaterial) == 0x38, "layout");

// BSLightingShaderMaterialBase: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI; class name and base from the image RTTI, 14 primary vftable slots
// sizeof BSLightingShaderMaterialBase 0xA0: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
// Create, CopyMembers, DoIsCopy, ComputeCRC32, GetDefault, GetFeature, GetType, OnLoadTextureSet, ClearTextures, ReceiveValuesFromRootMaterial, GetTextures, SaveBinary, LoadBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slots 01 to 0D
class BSLightingShaderMaterialBase : public BSShaderMaterial
{
public:
	// BSLightingShaderMaterialBase::BSLightingShaderMaterialBase: OBSERVED; called by Snow at 0x15235f0
	BSLightingShaderMaterialBase();
	~BSLightingShaderMaterialBase() override;  // 00
	BSShaderMaterial* Create() override;  // 01
	void CopyMembers(BSShaderMaterial* a_other) override;  // 02
	bool DoIsCopy(BSShaderMaterial* a_other) override;  // 03
	std::uint32_t ComputeCRC32() override;  // 04
	BSShaderMaterial* GetDefault() override;  // 05
	Feature GetFeature() const override;  // 06
	Type GetType() const override;  // 07
	virtual void OnLoadTextureSet(std::uint64_t a_arg1, BSTextureSet* a_textureSet);  // 08
	virtual void ClearTextures();  // 09
	virtual void ReceiveValuesFromRootMaterial(bool a_skinned, bool a_rimLighting, bool a_softLighting, bool a_backLighting, bool a_MSN);  // 0A
	virtual void GetTextures();  // 0B
	virtual void SaveBinary(NiStream& a_stream);  // 0C
	virtual void LoadBinary(NiStream& a_stream);  // 0D

	// unk38: GUESS(low); opaque base storage, no compared Snow function accesses it directly
	std::uint8_t unk38[0x68];  // 38
};
static_assert(sizeof(BSLightingShaderMaterialBase) == 0xA0, "layout");


class BSLightingShaderMaterialSnow : public BSLightingShaderMaterialBase
{
public:
    BSLightingShaderMaterialSnow();
    virtual Feature GetFeature() const;  // compared: 0x1528110
    virtual void CopyMembers(BSShaderMaterial* a_src);  // compared: 0x1528090
    BSLightingShaderMaterialSnow* Ctor();  // compared: 0x1527fc0
    virtual std::uint32_t ComputeCRC32();  // compared: 0x15280d0

    struct SnowData {
        std::uint64_t first;
        std::uint64_t second;
    };
    SnowData unknownA0;  // A0
};
static_assert(sizeof(BSLightingShaderMaterialSnow) == 0xB0, "BSLightingShaderMaterialSnow size");
