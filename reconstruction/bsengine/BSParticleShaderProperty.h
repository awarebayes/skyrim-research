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
// BSParticleShaderProperty declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-c2-s08-nirefobject-bsparticleshaderproperty
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSShaderProperty.h for BSShaderProperty.
// BSParticleShaderProperty: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSParticleShaderProperty::GetBaseTexture, BSParticleShaderProperty::SetupGeometry: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSParticleShaderProperty::particleShaderTexture: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG declares NiPointer<NiSourceTexture>, a raw pointer here, same size
// BSParticleShaderProperty::particleShaderGeometry: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG declares NiPointer<BSParticleShaderGeometry>, the compared code stores the BSGeometry* parameter as given
// BSGeometry: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); forward declaration only
// unknown88, unknown148, unknown170: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../bsengine/BSShaderProperty.h"

class BSGeometry;

class BSParticleShaderProperty : public BSShaderProperty
{
public:
    virtual std::uint32_t QShader() const;
    virtual NiSourceTexture* GetBaseTexture();  // compared: 0x1533bd0
    virtual bool SetupGeometry(BSGeometry* a_geometry);  // compared: 0x1532ca0

    std::uint8_t     unknown88[0xB8];       // 88
    NiSourceTexture* particleShaderTexture;  // 140
    std::uint8_t     unknown148[0x20];      // 148
    BSGeometry*      particleShaderGeometry;  // 168
    std::uint8_t     unknown170[0x28];      // 170
};
static_assert(sizeof(BSParticleShaderProperty) == 0x198, "BSParticleShaderProperty size");
