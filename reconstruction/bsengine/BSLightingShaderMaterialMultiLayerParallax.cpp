// BSLightingShaderMaterialMultiLayerParallax functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bslightingshadermaterialmultilayerparallax
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-normal-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5, worker haiku-202611122349-3), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0x1529070, 52 bytes: BSLightingShaderMaterialMultiLayerParallax::~BSLightingShaderMaterialMultiLayerParallax
//   RVA 0x15281a0, 102 bytes: BSLightingShaderMaterialMultiLayerParallax::Ctor (set aside in near-miss/0x15281a0.cpp)
//   RVA 0x1528820, 153 bytes: BSLightingShaderMaterialMultiLayerParallax::GetTextures (set aside in near-miss/0x1528820.cpp)
//   RVA 0x1528770, 163 bytes: BSLightingShaderMaterialMultiLayerParallax::ReceiveValuesFromRootMaterial
//   RVA 0x15284c0, 211 bytes: BSLightingShaderMaterialMultiLayerParallax::ComputeCRC32 (set aside in near-miss/0x15284c0.cpp)
//   RVA 0x15288d0, 292 bytes: BSLightingShaderMaterialMultiLayerParallax::SaveBinary (set aside in near-miss/0x15288d0.cpp)
//   RVA 0x1528a00, 324 bytes: BSLightingShaderMaterialMultiLayerParallax::LoadBinary (set aside in near-miss/0x1528a00.cpp)
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include <cstring>

#include "BSLightingShaderMaterialMultiLayerParallax.h"

// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared.
BSLightingShaderMaterialMultiLayerParallax::BSLightingShaderMaterialMultiLayerParallax()
{
}



// RVA 0x1528770, 163 bytes.
void BSLightingShaderMaterialMultiLayerParallax::ReceiveValuesFromRootMaterial(bool a_skinned, bool a_rimLighting, bool a_softLighting, bool a_backLighting, bool a_MSN, void* a_extra7, void* a_extra8)
{
	BaseReceiveValues(this, a_skinned, a_rimLighting, a_softLighting, a_backLighting, a_MSN, a_extra7, a_extra8);
	if (m_texA0 == nullptr) {
		NiSourceTexture* defaultTexture = g_defaultTexture._ptr;
		if (defaultTexture) {
			defaultTexture->IncRefCount();
			m_texA0 = defaultTexture;
		}
	}
	if (m_texA8 == nullptr) {
		NiSourceTexture* defaultMulti = g_defaultMultiLayerTexture._ptr;
		if (defaultMulti) {
			defaultMulti->IncRefCount();
			m_texA8 = defaultMulti;
		}
	}
	if (m_texB0 == nullptr) {
		NiSourceTexture* defaultTexture = g_defaultTexture._ptr;
		if (defaultTexture) {
			defaultTexture->IncRefCount();
			m_texB0 = defaultTexture;
		}
	}
}




// Retained generated leaf; its byte-match evidence is renewed with this unit.
// GetFeature: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
BSShaderMaterial::Feature BSLightingShaderMaterialMultiLayerParallax::GetFeature() const
{
    return static_cast<Feature>(0xb);
}
