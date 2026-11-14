// Build: sse-steam-1-7-104
// Source exposure: community-headers (layout reconciled with target allocation sizes separately).
// Drafted by GPT-6.1 Sol; p106 represented-layout recovery.
// Labels: v2
// Declaration source: CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a include/RE/B/BSLightingShaderMaterialBase.h; MIT.
// BSLightingShaderMaterialBase: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Member spelling and base declarations adapt that source; unspecified field meanings remain unknown.
// Omitted methods are not reconstructed. Pointee types are declarations only.
// Explicit padding fields are omitted; compiler alignment must satisfy every size and field assertion.
// Size assertions establish represented layout only, never a comparator match.
// MIT License
//
// Copyright (c) 2018 Ryan-rsm-McKenzie
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
// BSLightingShaderMaterialBaseLayout: GUESS(medium) STANDIN; represented layout type names
#pragma once
#include <cstdint>
#include <cstddef>
#include "bsengine/BSShaderMaterialLayout.h"
#include "bsengine/BSFixedStringLayout.h"

namespace ResearchLayouts {
class BSTextureSet;
class NiSourceTexture;
class BSLightingShaderMaterialBaseLayout : public BSShaderMaterialLayout {
public:
    virtual ~BSLightingShaderMaterialBaseLayout();
    NiColorLayout specularColor;
    NiPointerLayout<NiSourceTexture> diffuseTexture;
    std::int32_t diffuseRenderTargetSourceIndex;
    NiPointerLayout<NiSourceTexture> normalTexture;
    NiPointerLayout<NiSourceTexture> rimSoftLightingTexture;
    NiPointerLayout<NiSourceTexture> specularBackLightingTexture;
    std::int32_t textureClampMode;
    NiPointerLayout<BSTextureSet> textureSet;
    float materialAlpha;
    float refractionPower;
    float specularPower;
    float specularColorScale;
    float subSurfaceLightRolloff;
    float rimLightPower;
    std::uint64_t unk98;
};
static_assert(sizeof(BSLightingShaderMaterialBaseLayout) == 160, "community represented size");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, specularColor) == 56, "specularColor offset");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, diffuseTexture) == 72, "diffuseTexture offset");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, diffuseRenderTargetSourceIndex) == 80, "diffuseRenderTargetSourceIndex offset");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, normalTexture) == 88, "normalTexture offset");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, rimSoftLightingTexture) == 96, "rimSoftLightingTexture offset");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, specularBackLightingTexture) == 104, "specularBackLightingTexture offset");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, textureClampMode) == 112, "textureClampMode offset");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, textureSet) == 120, "textureSet offset");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, materialAlpha) == 128, "materialAlpha offset");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, refractionPower) == 132, "refractionPower offset");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, specularPower) == 136, "specularPower offset");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, specularColorScale) == 140, "specularColorScale offset");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, subSurfaceLightRolloff) == 144, "subSurfaceLightRolloff offset");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, rimLightPower) == 148, "rimLightPower offset");
static_assert(offsetof(BSLightingShaderMaterialBaseLayout, unk98) == 152, "unk98 offset");
}
