// BSLightingShaderMaterialBase type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Class, member and method names follow CharmedBaryon/CommonLibSSE-NG
// b93280e832f263dbef44e44cbe2936622a02f91a (MIT): include/RE/B/BSLightingShaderMaterialBase.h,
// BSShaderMaterial.h, NiBinaryStream.h, NiStream.h, NiSmartPointer.h, NiRefObject.h,
// NiColor.h. The declarations are minimal stand-ins, with two exceptions. The
// BSLightingShaderMaterialBase class declaration reproduces NG's full virtual and member list
// from include/RE/B/BSLightingShaderMaterialBase.h (MIT). The NiBinaryStream ReadFn and WriteFn
// aliases and the read, write, binary_read and binary_write bodies are adapted from NG b93280e
// include/RE/N/NiBinaryStream.h and src/RE/N/NiBinaryStream.cpp under its MIT licence (asserts
// dropped, binary_read and binary_write defined inline). NiRefObject's IncRefCount and
// DecRefCount follow the logic of NG src/RE/N/NiRefObject.cpp, written here with compiler
// intrinsics; they also closely parallel the inline NiRefObject reference-count bodies of
// momusdigital/fnv_decomp 91e1b6e8 (no licence; used by maintainer decision,
// docs/authorizations.md), which tools/check_origin.py reports at similarity 0.86 and 0.78. The
// Sibling source lines below declare that parallel; they do not record a copy.
// Bodies adapted from community sources are listed above; tools/check_origin.py reports none
// other above its threshold (0.75) at CommonLibSSE-NG b93280e, powerof3/CommonLibSSE 654e55f
// and momusdigital/fnv_decomp 91e1b6e8. NG's licence notice, from its LICENSE at b93280e, is
// kept as it requires:
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
// The vtable order comes from the image RTTI and vftables; the class sizes (0x38 and 0xA0) come
// from the size argument of operator delete in each deleting destructor.
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/bsshader/boltshader.cpp:27
// Sibling source: momusdigital/fnv_decomp@91e1b6e8 src/bsshader/boltshader.cpp:31
// Stand-ins: BSShaderMaterial (name from the image RTTI, layout from NG), NiSourceTexture,
// NiRefObject, NiPointer, NiColor, NiBinaryStream, NiStream; BSTextureSet is only declared.
// BSLightingShaderMaterialBase: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI; each declaration below carries its own label
#pragma once

#include <cstdint>

#include <intrin.h>

// NiRefObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiRefObject::DeleteThis, ::IncRefCount, ::DecRefCount, ::_refCount: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiRefObject
{
public:
	virtual ~NiRefObject();  // 00
	virtual void DeleteThis();  // 01

	void IncRefCount()
	{
		// atomic: references are shared across loader threads
		_InterlockedIncrement(reinterpret_cast<volatile long*>(&_refCount));
	}

	void DecRefCount()
	{
		// atomic: the last releaser deletes the object
		if (_InterlockedExchangeAdd(reinterpret_cast<volatile long*>(&_refCount), -1) == 1) {
			DeleteThis();
		}
	}

	volatile std::uint32_t _refCount;  // 08
	std::uint32_t          _pad0C;     // 0C
};

// NiSourceTexture: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the base is needed
class NiSourceTexture : public NiRefObject
{
};

// NiPointer: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// _ptr: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG declares it protected in a different shape
// operator=: take the new reference before releasing the old one, so an assignment whose old
// object holds the last reference to the new one never frees the new one first
template <class T>
class NiPointer
{
public:
	NiPointer& operator=(const NiPointer& a_rhs)
	{
		T* old = _ptr;
		T* incoming = a_rhs._ptr;
		if (old != incoming) {
			if (incoming) {
				incoming->IncRefCount();
			}
			_ptr = incoming;
			if (old) {
				old->DecRefCount();
			}
		}
		return *this;
	}

	explicit operator bool() const { return _ptr != nullptr; }

	T* _ptr;  // 00
};

// BSTextureSet: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); declared only, no compared function uses its members
class BSTextureSet;

// NiColor: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiColor::SaveBinary2, NiColor::LoadBinary2: GUESS(low); the image calls helpers taking
// (NiColor*, NiStream*) at 0xef2fd0 and 0xef2f10 whose names no community source gives
// red, green, blue: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiStream;
class NiColor
{
public:
	void SaveBinary2(NiStream& a_stream) const;
	void LoadBinary2(NiStream& a_stream);

	float red;    // 0
	float green;  // 4
	float blue;   // 8
};

// NiBinaryStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiBinaryStream::read, ::write, ::binary_read, ::binary_write, ::_absoluteCurrentPos, ::_readFn,
// ::_writeFn: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiBinaryStream::good, ::seek, ::tell, ::get_info, ::set_endian_swap, ::_pad0C: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); get_info takes NG's BufferInfo&, left without parameters here
class NiBinaryStream
{
public:
	using ReadFn = std::uint32_t(NiBinaryStream* a_this, void* a_buffer, std::uint32_t a_bytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents);
	using WriteFn = std::uint32_t(NiBinaryStream* a_this, const void* a_buffer, std::uint32_t a_bytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents);

	template <class CharT>
	bool read(CharT* a_str, std::uint32_t a_count)
	{
		std::uint32_t size = sizeof(CharT);
		std::uint32_t toRead = a_count * size;
		std::uint32_t bytesRead = binary_read(a_str, toRead, &size);
		return bytesRead == toRead;
	}

	template <class CharT>
	bool write(const CharT* a_str, std::uint32_t a_count)
	{
		std::uint32_t size = sizeof(CharT);
		std::uint32_t toWrite = a_count * size;
		std::uint32_t bytesWritten = binary_write(a_str, toWrite, &size);
		return bytesWritten == toWrite;
	}

	std::uint32_t binary_read(void* a_buffer, std::uint32_t a_totalBytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents = 1)
	{
		std::uint32_t bytesRead = _readFn(this, a_buffer, a_totalBytes, a_componentSizes, a_numComponents);
		_absoluteCurrentPos += bytesRead;
		return bytesRead;
	}

	std::uint32_t binary_write(const void* a_buffer, std::uint32_t a_totalBytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents = 1)
	{
		std::uint32_t bytesWritten = _writeFn(this, a_buffer, a_totalBytes, a_componentSizes, a_numComponents);
		_absoluteCurrentPos += bytesWritten;
		return bytesWritten;
	}

	virtual ~NiBinaryStream();      // 00
	virtual bool good() const = 0;  // 01
	virtual void seek(std::int32_t a_numBytes) = 0;  // 02
	virtual std::uint32_t tell() const;  // 03
	virtual void get_info();  // 04
	virtual void set_endian_swap(bool a_doSwap) = 0;  // 05

	std::uint32_t _absoluteCurrentPos;  // 08
	std::uint32_t _pad0C;               // 0C
	ReadFn*       _readFn;              // 10
	WriteFn*      _writeFn;             // 18
};

// NiStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiStream::iStr, ::oStr: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unk08: GUESS(low); members before the two stream pointers, sized so they land at 0x298 and 0x2A0
class NiStream
{
public:
	virtual ~NiStream();  // 00

	std::uint8_t    unk08[0x290];  // 08
	NiBinaryStream* iStr;          // 298
	NiBinaryStream* oStr;          // 2A0
};

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

// g_defaultLightingMaterial, g_defaultTexture, g_defaultBackLightingTexture: GUESS(low); the image reads a default material pointer and two default texture
// pointers from fixed .data addresses (0x33d4db0, 0x3336448, 0x3336428). Bound by hint to those RVAs.
extern BSShaderMaterial* g_defaultLightingMaterial;
extern NiPointer<NiSourceTexture> g_defaultTexture;
extern NiPointer<NiSourceTexture> g_defaultBackLightingTexture;

// BSLightingShaderMaterialBase: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI; class name and base from the image RTTI, 14 primary vftable slots
// sizeof BSLightingShaderMaterialBase 0xA0: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
// Create, CopyMembers, DoIsCopy, ComputeCRC32, GetDefault, GetFeature, GetType, OnLoadTextureSet, ClearTextures, ReceiveValuesFromRootMaterial, GetTextures, SaveBinary, LoadBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slots 01 to 0D
// specularColor, pad44, diffuseTexture, diffuseRenderTargetSourceIndex, pad54, normalTexture, rimSoftLightingTexture, specularBackLightingTexture: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG's members at the same offsets
// textureClampMode, pad74, textureSet, materialAlpha, refractionPower, specularPower, specularColorScale, subSurfaceLightRolloff, rimLightPower, unk98: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG's members at the same offsets
class BSLightingShaderMaterialBase : public BSShaderMaterial
{
public:
	// constructor: GUESS(low); declared so the deleting destructor and vftable are emitted
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

	NiColor                    specularColor;                   // 38
	std::uint32_t              pad44;                           // 44
	NiPointer<NiSourceTexture> diffuseTexture;                  // 48
	std::int32_t               diffuseRenderTargetSourceIndex;  // 50
	std::uint32_t              pad54;                           // 54
	NiPointer<NiSourceTexture> normalTexture;                   // 58
	NiPointer<NiSourceTexture> rimSoftLightingTexture;          // 60
	NiPointer<NiSourceTexture> specularBackLightingTexture;     // 68
	std::int32_t               textureClampMode;                // 70
	std::int32_t               pad74;                           // 74
	NiPointer<BSTextureSet>    textureSet;                      // 78
	float                      materialAlpha;                   // 80
	float                      refractionPower;                 // 84
	float                      specularPower;                   // 88
	float                      specularColorScale;              // 8C
	float                      subSurfaceLightRolloff;          // 90
	float                      rimLightPower;                   // 94
	std::uint64_t              unk98;                           // 98
};
static_assert(sizeof(BSLightingShaderMaterialBase) == 0xA0, "layout");
