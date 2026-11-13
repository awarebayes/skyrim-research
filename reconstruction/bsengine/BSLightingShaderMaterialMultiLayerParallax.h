// BSLightingShaderMaterialMultiLayerParallax declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bslightingshadermaterialmultilayerparallax
// Source exposure: mixed (class and member names from community headers; sizes, offsets and the
// compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: the derived members and the stand-ins below carry only
// what the compared code touches; community names are unverified.
// Base form: shared header ../bsengine/BSLightingShaderMaterialBase.h for BSLightingShaderMaterialBase
// and its NiStream, NiBinaryStream and NiPointer stand-ins.
// BSLightingShaderMaterialMultiLayerParallax: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSLightingShaderMaterialMultiLayerParallax::~BSLightingShaderMaterialMultiLayerParallax, BSLightingShaderMaterialMultiLayerParallax::Ctor, BSLightingShaderMaterialMultiLayerParallax::GetTextures, BSLightingShaderMaterialMultiLayerParallax::ReceiveValuesFromRootMaterial, BSLightingShaderMaterialMultiLayerParallax::ComputeCRC32, BSLightingShaderMaterialMultiLayerParallax::SaveBinary, BSLightingShaderMaterialMultiLayerParallax::LoadBinary: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../bsengine/BSLightingShaderMaterialBase.h"

// BSTextureSetSlots: STANDIN GUESS(low)
// Only the vtable slot the compared code calls is named. Slot 0x128 is 37 * 8, so 37 placeholder slots precede it.
class BSTextureSetSlots
{
public:
	// unk00 through unk36: GUESS(low)
	virtual void unk00();
	virtual void unk01();
	virtual void unk02();
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
	virtual void unk17();
	virtual void unk18();
	virtual void unk19();
	virtual void unk1A();
	virtual void unk1B();
	virtual void unk1C();
	virtual void unk1D();
	virtual void unk1E();
	virtual void unk1F();
	virtual void unk20();
	virtual void unk21();
	virtual void unk22();
	virtual void unk23();
	virtual void unk24();
	// GetCRCSource: GUESS(low); the value is passed on to CRCTermFromValue
	virtual std::uint64_t GetCRCSource(std::uint32_t a_flag);
};

// Helpers the compared code calls directly; the image addresses are in bind-hints.json.
// BSLightingShaderMaterial_Ctor: GUESS(low); enclosing BSLightingShaderMaterial::Ctor in CharmedBaryon/CommonLibSSE-NG@b93280e (MIT)
void BSLightingShaderMaterial_Ctor(BSLightingShaderMaterialBase* a_self);
// BaseReceiveValues: GUESS(low); called with this, the five bool arguments and two pointer-sized arguments
void BaseReceiveValues(BSLightingShaderMaterialBase* a_self, bool a_skinned, bool a_rimLighting, bool a_softLighting, bool a_backLighting, bool a_MSN, void* a_extra7, void* a_extra8);
// CRCTermFromValue: GUESS(low)
void CRCTermFromValue(std::uint32_t* a_out, std::uint64_t a_value, std::uint32_t a_flags);
// ComputeCRCBase: GUESS(low)
std::uint32_t ComputeCRCBase(BSLightingShaderMaterialBase* a_self, std::uint32_t a_seed);
// CRC32Calculator_SizeOfSize: GUESS(low); the result is written through the first argument
void CRC32Calculator_SizeOfSize(std::uint32_t* a_out, const void* a_data, std::uint32_t a_size);

// Image data: the vtable of this class and the two default textures read by ReceiveValues.
// g_BSLightingShaderMaterialMultiLayerParallaxVtable: GUESS(low); address of the first vtable slot
extern void* const g_BSLightingShaderMaterialMultiLayerParallaxVtable[1];
// g_defaultMultiLayerTexture: GUESS(low); the second default texture read at 0x3336430
extern NiPointer<NiSourceTexture> g_defaultMultiLayerTexture;

class BSLightingShaderMaterialMultiLayerParallax : public BSLightingShaderMaterialBase
{
public:
    // GetFeature: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
    Feature GetFeature() const override;
	BSLightingShaderMaterialMultiLayerParallax();
	// the deleting destructor (slot 0) is emitted with the constructor; the plain one is external
	virtual ~BSLightingShaderMaterialMultiLayerParallax();  // compared: 0x1529070 (scalar deleting destructor)
	// Ctor: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); returns this after the base constructor
	BSLightingShaderMaterialMultiLayerParallax* Ctor();  // compared: 0x15281a0
	// GetTextures: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); takes an output array and returns the number of textures written
	virtual std::uint32_t GetTextures(NiSourceTexture** a_textures);  // compared: 0x1528820
	// ReceiveValuesFromRootMaterial: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the image takes two more pointer-sized arguments
	virtual void ReceiveValuesFromRootMaterial(bool a_skinned, bool a_rimLighting, bool a_softLighting, bool a_backLighting, bool a_MSN, void* a_extra7, void* a_extra8);  // compared: 0x1528770
	// ComputeCRC32: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the image takes one 32-bit argument
	virtual std::uint32_t ComputeCRC32(std::uint32_t a_seed);  // compared: 0x15284c0
	virtual void SaveBinary(NiStream& a_stream);  // compared: 0x15288d0
	virtual void LoadBinary(NiStream& a_stream);  // compared: 0x1528a00

	// m_texA0, m_texA8, m_texB0: GUESS(low); reference-counted textures stored without release
	NiSourceTexture* m_texA0;  // 0xA0
	NiSourceTexture* m_texA8;  // 0xA8
	NiSourceTexture* m_texB0;  // 0xB0
	// m_flagB8: GUESS(low); written as a dword and read as a dword
	std::uint32_t m_flagB8;  // 0xB8
	// m_fBC, m_fC0, m_fC4, m_fC8: GUESS(low); floats that the constructor sets to 1.0
	float m_fBC;  // 0xBC
	float m_fC0;  // 0xC0
	float m_fC4;  // 0xC4
	float m_fC8;  // 0xC8
	// unkCC: GUESS(low); padding up to the size check
	std::uint8_t unkCC[0x4];  // 0xCC
};
static_assert(sizeof(BSLightingShaderMaterialMultiLayerParallax) == 0xD0, "BSLightingShaderMaterialMultiLayerParallax size");
