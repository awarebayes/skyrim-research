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
// BSGrassShaderProperty declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-c2-s08-nirefobject-bsgrassshaderproperty
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../bsengine/BSShaderProperty.h for BSShaderProperty.
// BSGrassShaderProperty: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0) EXE_RTTI
// BSLightingShaderProperty: STANDIN EXE_RTTI
// BSGrassShaderProperty::IsEqual: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
// unknown88: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../bsengine/BSShaderProperty.h"

class BSLightingShaderProperty : public BSShaderProperty
{
public:
};

class BSGrassShaderProperty : public BSLightingShaderProperty
{
public:
    virtual std::uint32_t QShader() const;
    virtual bool IsEqual(NiObject* a_object);  // compared: 0x151d6d0

    // TODO members: replace part of the padding with the members the bodies read,
    // keeping every offset and the size check true.
    std::uint8_t unknown88[0x148];  // 88
};
static_assert(sizeof(BSGrassShaderProperty) == 0x1D0, "BSGrassShaderProperty size");
