// BSShaderProperty member functions for build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Drafted by claude-sonnet-5-5.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json
// Compared functions:
//   RVA 0x14e85f0, 6 bytes: ForEachTexture
//   RVA 0x14e8680, 9 bytes: QMaterialAlpha
//   RVA 0x14e7fb0, 66 bytes: DoClearRenderPasses
//   RVA 0x14e7ef0, 73 bytes: SetFlags
//   RVA 0x14e7450, 120 bytes: SaveBinary
//   RVA 0x14e7390, 147 bytes: LoadBinary
// Evidence: findings/fourth-batch-selection.md
// Names are as labelled in BSShaderProperty.h. Bodies are written from the image; none is adapted
// from a community source; tools/check_origin.py reports none above its threshold at
// CommonLibSSE-NG b93280e, powerof3/CommonLibSSE 654e55f and momusdigital/fnv_decomp 91e1b6e8.
// Unbound targets are bound by position or hint: ClearRenderPass 0x1555920, the NiShadeProperty
// stream bases 0xf0edf0 and 0xf0ee20, and NiPoint2 LoadBinary 0xeecd50 / SaveBinary 0xeecde0.
// SetMaterial (0x14e8000) is not compared here; see the task's near-miss file.
// The braces in SaveBinary end the component-size local before the last call so the compiler
// emits it as a tail call, as the image does.
#include "BSShaderProperty.h"

#include <climits>

float BSShaderProperty::QMaterialAlpha()
{
	return 1.0f;
}

std::int32_t BSShaderProperty::ForEachTexture(ForEachVisitor&)
{
	return 1;
}

void BSShaderProperty::DoClearRenderPasses()
{
	for (BSRenderPass* pass = renderPassList.head; pass;) {
		BSRenderPass* next = pass->next;
		pass->ClearRenderPass();
		pass = next;
	}
	lastRenderPassState = INT_MAX;
	renderPassList.head = nullptr;
}

void BSShaderProperty::SetFlags(EShaderPropertyFlag8 a_flag, bool a_set)
{
	const std::uint64_t bit = std::uint64_t(1) << static_cast<std::uint32_t>(a_flag);
	if (a_set) {
		if (!(flags & bit)) {
			lastRenderPassState = INT_MAX;
		}
		flags |= bit;
	} else {
		if (flags & bit) {
			lastRenderPassState = INT_MAX;
		}
		flags &= ~bit;
	}
}

void BSShaderProperty::LoadBinary(NiStream& a_stream)
{
	BSShaderMaterial* mat = material;
	NiShadeProperty::LoadBinary(a_stream);
	NiBinaryStream* in = a_stream.iStr;
	std::uint32_t componentSize = 8;
	in->binary_read(&flags, 8, &componentSize, 1);
	mat->texCoordOffset[0].LoadBinary(a_stream);
	mat->texCoordScale[0].LoadBinary(a_stream);
	mat->texCoordOffset[1] = mat->texCoordOffset[0];
	mat->texCoordScale[1] = mat->texCoordScale[0];
}

void BSShaderProperty::SaveBinary(NiStream& a_stream)
{
	NiShadeProperty::SaveBinary(a_stream);
	{
		NiBinaryStream* out = a_stream.oStr;
		std::uint32_t componentSize = 8;
		out->binary_write(&flags, 8, &componentSize, 1);
	}
	material->texCoordOffset[0].SaveBinary(&a_stream);
	material->texCoordScale[0].SaveBinary(&a_stream);
}
