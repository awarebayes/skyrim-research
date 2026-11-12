// BGSHeadPart type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT). TESForm comes from
// the shared header; only the members and slots the compared code needs are declared here.
// Adapted body: BSFixedString::c_str (the null test with the empty-string fallback), from
// CharmedBaryon/CommonLibSSE-NG@b93280e include/RE/B/BSFixedString.h, MIT. Licence notice:
//
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
//
// Other bodies adapted from community sources: none; tools/check_origin.py reports none above its
// threshold at the pinned checkouts.
// BGSHeadPart, BGSHeadPart::GetFormEditorID, ::SetFormEditorID, ::formEditorID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSHeadPart::unk20: GUESS(low); filler bytes for the TESFullName, TESModelTextureSwap bases and the data members up to offset 0x118
// BSFixedString, BSFixedString::c_str, ::operator=, ::_data: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; a single string pointer; operator= is declared and not defined, bound by hint to 0xeb1120
#pragma once

#include <cstdint>

#include "TESForm.h"

class BSFixedString {
public:
    BSFixedString& operator=(const char* a_str);

    const char* c_str() const { return _data ? _data : ""; }

    const char* _data;  // 00
};

class BGSHeadPart : public TESForm {
public:
    const char* GetFormEditorID() const override;             // 32
    bool        SetFormEditorID(const char* a_str) override;  // 33

    std::uint8_t  unk20[0xF8];   // 20
    BSFixedString formEditorID;  // 118
};
