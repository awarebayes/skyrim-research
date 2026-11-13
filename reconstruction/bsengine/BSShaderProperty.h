// BSShaderProperty type declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Class, member and virtual names follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT)
// include/RE/B/BSShaderProperty.h, include/RE/N/NiStream.h and include/RE/N/NiBinaryStream.h.
// Layout sizes and offsets are from the image. NiBinaryStream::binary_read and binary_write
// are adapted from CharmedBaryon/CommonLibSSE-NG b93280e src/RE/N/NiBinaryStream.cpp (MIT).
// tools/check_origin.py reports no further bodies above its threshold at CommonLibSSE-NG
// b93280e, powerof3/CommonLibSSE 654e55f and momusdigital/fnv_decomp 91e1b6e8.
// Shared header: ../netimmerse/NiObject.h supplies NiObject and NiRefObject.
// NiObjectNET, NiProperty, NiShadeProperty, NiStream, NiBinaryStream, NiPoint2, BSShaderMaterial,
// BSRenderPass, ForEachVisitor: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSShaderProperty: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// SetFlags, SetMaterial, DoClearRenderPasses, QMaterialAlpha, ForEachTexture, LoadBinary, SaveBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// alpha, lastRenderPassState, flags, renderPassList, material: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// EShaderPropertyFlag8, kSpecular: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// iStr, oStr, next, controllers, texCoordOffset, texCoordScale: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// ClearRenderPass: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); GPL-3.0 applies to the name in this file
// binary_read, binary_write: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; the image reads the function pointer at 0x10 or 0x18 and advances the position at 8
// Adapted body: NiBinaryStream::binary_read, from CharmedBaryon/CommonLibSSE-NG b93280e src/RE/N/NiBinaryStream.cpp (MIT), with the
// assert dropped; binary_write follows it. NG's licence notice from its LICENSE at b93280e:
//   MIT License
//   Copyright (c) 2018 Ryan-rsm-McKenzie
//   Permission is hereby granted, free of charge, to any person obtaining a copy
//   of this software and associated documentation files (the "Software"), to deal
//   in the Software without restriction, including without limitation the rights
//   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
//   copies of the Software, and to permit persons to whom the Software is
//   furnished to do so, subject to the following conditions:
//   The above copyright notice and this permission notice shall be included in all
//   copies or substantial portions of the Software.
//   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
//   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
//   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
//   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
//   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
//   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
//   SOFTWARE.
// NiPoint2::LoadBinary, NiPoint2::SaveBinary: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); names and stream parameter forms from include/NiPoint2.h, the Skyrim callees are unnamed
// g_shaderMaterialManager, ShaderMaterialManager, AcquireMaterial, ReleaseMaterial: GUESS(low); the image calls a method on a global with (material, flag, flag) and one with (material)
#pragma once

#include <cstdint>
#include "../netimmerse/NiObject.h"

class NiStream;
class BSShaderMaterial;
class BSRenderPass;
class NiSourceTexture;

// NiBinaryStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiBinaryStream
{
public:
	virtual ~NiBinaryStream();  // 00

	std::uint32_t binary_read(void* a_buffer, std::uint32_t a_totalBytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents = 1)
	{
		const std::uint32_t bytesRead = _readFn(this, a_buffer, a_totalBytes, a_componentSizes, a_numComponents);
		_absoluteCurrentPos += bytesRead;
		return bytesRead;
	}

	std::uint32_t binary_write(const void* a_buffer, std::uint32_t a_totalBytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents = 1)
	{
		const std::uint32_t bytesWritten = _writeFn(this, a_buffer, a_totalBytes, a_componentSizes, a_numComponents);
		_absoluteCurrentPos += bytesWritten;
		return bytesWritten;
	}

	using ReadFn = std::uint32_t(NiBinaryStream*, void*, std::uint32_t, std::uint32_t*, std::uint32_t);
	using WriteFn = std::uint32_t(NiBinaryStream*, const void*, std::uint32_t, std::uint32_t*, std::uint32_t);

	std::uint32_t _absoluteCurrentPos;  // 08
	std::uint32_t _pad0C;               // 0C
	ReadFn*       _readFn;              // 10
	WriteFn*      _writeFn;             // 18
};
static_assert(sizeof(NiBinaryStream) == 0x20, "NiBinaryStream size");

// NiStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the two stream pointers are declared
class NiStream
{
public:
	virtual ~NiStream();  // 00

	std::uint8_t    unk08[0x290];  // 08
	NiBinaryStream* iStr;          // 298
	NiBinaryStream* oStr;          // 2A0
};
static_assert(sizeof(NiStream) == 0x2A8, "NiStream stand-in size");

// NiPoint2: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the stream helpers are labelled in the header comment
struct NiPoint2
{
	float x;  // 00
	float y;  // 04

	void LoadBinary(NiStream& a_stream);
	void SaveBinary(NiStream* a_stream);
};

// BSShaderMaterial: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class BSShaderMaterial
{
public:
	virtual ~BSShaderMaterial();  // 00

	std::uint32_t refCount;           // 08
	NiPoint2      texCoordOffset[2];  // 0C
	NiPoint2      texCoordScale[2];   // 1C
	std::uint32_t hashKey;            // 2C
	std::uint32_t unk30;              // 30
	std::uint32_t unk34;              // 34
};
static_assert(sizeof(BSShaderMaterial) == 0x38, "BSShaderMaterial size");

// BSRenderPass: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only next and ClearRenderPass are declared
class BSRenderPass
{
public:
	void ClearRenderPass();

	std::uint8_t  unk00[0x28];  // 00
	BSRenderPass* next;         // 28
};

// ShaderMaterialManager: STANDIN GUESS(low); owner of the material cache the global points at
class ShaderMaterialManager
{
public:
	BSShaderMaterial* AcquireMaterial(BSShaderMaterial* a_material, bool a_flag, bool a_unk);
	void              ReleaseMaterial(BSShaderMaterial* a_material);
};

extern ShaderMaterialManager* g_shaderMaterialManager;

// NiObjectNET: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiObjectNET : public NiObject
{
public:
	~NiObjectNET() override;  // 00
	void LoadBinary(NiStream& a_stream) override;  // 18
	void SaveBinary(NiStream& a_stream) override;  // 1B

	const void*    name;            // 10
	void*          controllers;     // 18
	void**         extra;           // 20
	std::uint16_t  extraDataSize;   // 28
	std::uint16_t  maxExtraData;    // 2A
	std::uint32_t  pad2C;           // 2C
};
static_assert(sizeof(NiObjectNET) == 0x30, "NiObjectNET size");

// NiProperty: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiProperty : public NiObjectNET
{
public:
	~NiProperty() override;  // 00
	virtual void GetType();  // 25
	virtual void Update();   // 26
};

// NiShadeProperty: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiShadeProperty : public NiProperty
{
public:
	~NiShadeProperty() override;  // 00
	void LoadBinary(NiStream& a_stream) override;  // 18
	void SaveBinary(NiStream& a_stream) override;  // 1B
	virtual void SetupGeometry();        // 27
	virtual void FinishSetupGeometry();  // 28
	virtual void Unk_29();               // 29
};

// EShaderPropertyFlag8: OBSERVED; the image shifts by the whole register, NG declares std::uint8_t
enum class EShaderPropertyFlag8 : std::uint32_t
{
	kSpecular = 0
};

class BSShaderProperty : public NiShadeProperty
{
public:
	class ForEachVisitor
	{
	public:
		virtual ~ForEachVisitor();  // 00
	};

	struct RenderPassArray
	{
		BSRenderPass* head;  // 0
	};

	~BSShaderProperty() override;  // 00
	void LoadBinary(NiStream& a_stream) override;  // 18
	void SaveBinary(NiStream& a_stream) override;  // 1B

	virtual void         GetRenderPasses();  // 2A
	virtual void         Unk_2B();           // 2B
	virtual void         Unk_2C();           // 2C
	virtual void         Unk_2D();           // 2D
	virtual void         Unk_2E();           // 2E
	virtual void         Unk_2F();           // 2F
	virtual void         CanMerge();         // 30
	virtual void         SetMaterialAlpha(); // 31
	virtual float        QMaterialAlpha();   // 32
	virtual std::int32_t ForEachTexture(ForEachVisitor& a_visitor);  // 33
	virtual void         DoClearRenderPasses();  // 34

	void SetMaterial(BSShaderMaterial* a_material, bool a_unk1);
	void SetFlags(EShaderPropertyFlag8 a_flag, bool a_set);

	float           alpha;                // 30
	std::int32_t    lastRenderPassState;  // 34
	std::uint64_t   flags;                // 38
	RenderPassArray renderPassList;       // 40
	std::uint8_t    unk48[0x30];          // 48
	BSShaderMaterial* material;           // 78
	std::uint64_t   unk80;                // 80
};
static_assert(sizeof(BSShaderProperty) == 0x88, "BSShaderProperty size");
