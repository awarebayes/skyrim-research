// BGSMusicType type declarations, build sse-steam-1-7-104.
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
// BGSMusicType, BGSMusicType::GetFormEditorID, BGSMusicType::SetFormEditorID, BGSMusicType::DoPause, BGSMusicType::~BGSMusicType, BGSMusicType::formEditorID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSIMusicType, BSIMusicType::DoUpdate, ::DoPlay, ::DoPause, ::DoFinish, ::DoApplyDuckingAttenuation, ::DoClearDucking, ::DoPrepare, ::flags, ::priority, ::ducksOtherMusicBy, ::fadeTime, ::currentTrackIndex, ::trackHistory, ::tracks, ::typeStatus: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); layout as in NG, size 0x50
// BSIMusicType::padding, ::pad4C: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); padding
// BSIMusicType::~BSIMusicType: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); last slot, 07
// BSIMusicTrack, BSIMusicTrack::DoUpdate, ::DoPlay, ::DoPause: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the slot order 00 to 03 is claimed
// BSTArray, BSTArray::operator[]: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; layout data, capacity, size read from the listing
// BSTArray::_size: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; public here
// BSTArray::_data, ::_capacity, ::pad0C, ::pad14: GUESS(low); the allocator pointer, capacity and padding
// BSFixedString, BSFixedString::c_str, ::operator=, ::_data: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; a single string pointer; operator= is declared and not defined, bound by hint to 0xeb1120
// BGSMusicType::BGSMusicType: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); name only, defined only so the unit emits the vftables and with them the destructor thunk
#pragma once

#include <cstdint>

#include "TESForm.h"

class BSFixedString {
public:
    BSFixedString& operator=(const char* a_str);

    const char* c_str() const { return _data ? _data : ""; }

    const char* _data;  // 00
};

class BSIMusicTrack {
public:
    virtual ~BSIMusicTrack();     // 00
    virtual void DoUpdate();      // 01
    virtual void DoPlay();        // 02
    virtual void DoPause();       // 03
};

template <class T>
struct BSTArray {
    T& operator[](std::uint32_t a_pos) { return _data[a_pos]; }

    T*            _data;      // 00
    std::uint32_t _capacity;  // 08
    std::uint32_t pad0C;      // 0C
    std::uint32_t _size;      // 10
    std::uint32_t pad14;      // 14
};

class BSIMusicType {
public:
    virtual void DoUpdate();                                      // 00
    virtual void DoPlay();                                        // 01
    virtual void DoPause();                                       // 02
    virtual void DoFinish(bool a_arg1);                           // 03
    virtual void DoApplyDuckingAttenuation(std::uint16_t a_ducking);  // 04
    virtual void DoClearDucking();                                // 05
    virtual void DoPrepare();                                     // 06
    virtual ~BSIMusicType();                                      // 07

    std::uint32_t            flags;              // 08
    std::uint8_t             priority;           // 0C
    std::uint8_t             padding;            // 0D
    std::uint16_t            ducksOtherMusicBy;  // 0E
    float                    fadeTime;           // 10
    std::uint32_t            currentTrackIndex;  // 14
    BSTArray<std::uint32_t>  trackHistory;       // 18
    BSTArray<BSIMusicTrack*> tracks;             // 30
    std::uint32_t            typeStatus;         // 48
    std::uint32_t            pad4C;              // 4C
};
static_assert(sizeof(BSIMusicType) == 0x50, "layout");

class BGSMusicType :
    public TESForm,      // 00
    public BSIMusicType  // 20
{
public:
    BGSMusicType();
    ~BGSMusicType() override;  // 00

    const char* GetFormEditorID() const override;             // 32
    bool        SetFormEditorID(const char* a_str) override;  // 33

    void DoPause() override;  // BSIMusicType 02

    BSFixedString formEditorID;  // 70
};
static_assert(sizeof(BGSMusicType) == 0x78, "layout");
