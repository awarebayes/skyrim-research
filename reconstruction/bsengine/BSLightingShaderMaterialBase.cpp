// BSLightingShaderMaterialBase member functions, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x4b4ad0, 6 bytes (GetType); RVA 0x1523d10, 8 bytes (GetDefault);
// RVA 0x1523f00, 191 bytes (ReceiveValuesFromRootMaterial);
// RVA 0x1524030, 396 bytes (SaveBinary); RVA 0x15241d0, 396 bytes (LoadBinary).
// Evidence: findings/fourth-batch-selection.md (class row; per-function evidence is in the private packs).
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with the class layout from the header beside this file.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. Five functions are compared; ClearTextures, OnLoadTextureSet and CopyMembers are not.
// Names follow CommonLibSSE-NG (CharmedBaryon/CommonLibSSE-NG@b93280e, MIT).
#include "BSLightingShaderMaterialBase.h"

BSLightingShaderMaterialBase::Type BSLightingShaderMaterialBase::GetType() const
{
	return Type::kLighting;
}

BSShaderMaterial* BSLightingShaderMaterialBase::GetDefault()
{
	return g_defaultLightingMaterial;
}

void BSLightingShaderMaterialBase::ReceiveValuesFromRootMaterial(bool a_skinned, bool a_rimLighting, bool a_softLighting, bool a_backLighting, bool a_MSN)
{
	if (!diffuseTexture) {
		diffuseTexture = g_defaultTexture;
	}
	if (!normalTexture) {
		normalTexture = g_defaultTexture;
	}
	if (a_rimLighting && !rimSoftLightingTexture) {
		rimSoftLightingTexture = g_defaultTexture;
	}
	if (a_softLighting && !rimSoftLightingTexture) {
		rimSoftLightingTexture = g_defaultTexture;
	}
	if (a_backLighting && !specularBackLightingTexture) {
		specularBackLightingTexture = g_defaultTexture;
	}
	if (a_skinned && a_MSN && !specularBackLightingTexture) {
		specularBackLightingTexture = g_defaultBackLightingTexture;
	}
}

void BSLightingShaderMaterialBase::SaveBinary(NiStream& a_stream)
{
	a_stream.oStr->write(&textureClampMode, 1);
	a_stream.oStr->write(&materialAlpha, 1);
	a_stream.oStr->write(&refractionPower, 1);
	a_stream.oStr->write(&specularPower, 1);
	specularColor.SaveBinary2(a_stream);
	a_stream.oStr->write(&specularColorScale, 1);
	a_stream.oStr->write(&subSurfaceLightRolloff, 1);
	a_stream.oStr->write(&rimLightPower, 1);
}

void BSLightingShaderMaterialBase::LoadBinary(NiStream& a_stream)
{
	a_stream.iStr->read(&textureClampMode, 1);
	a_stream.iStr->read(&materialAlpha, 1);
	a_stream.iStr->read(&refractionPower, 1);
	a_stream.iStr->read(&specularPower, 1);
	specularColor.LoadBinary2(a_stream);
	a_stream.iStr->read(&specularColorScale, 1);
	a_stream.iStr->read(&subSurfaceLightRolloff, 1);
	a_stream.iStr->read(&rimLightPower, 1);
}
