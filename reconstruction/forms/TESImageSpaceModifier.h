// TESImageSpaceModifier type declaration, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESImageSpaceModifier.h
// and include/RE/B/BSString.h. The destructor is declared without a body in this unit: the deleting
// destructor calls the plain one at RVA 0x2a6d30, bound by hint. Members before the editor ID are not recovered.
// Adapted bodies: none declared.
// TESImageSpaceModifier, TESImageSpaceModifier::GetFormEditorID, ::SetFormEditorID, ::~TESImageSpaceModifier, ::formEditorID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESImageSpaceModifier::unk20: GUESS(low); stands for the members from 0x20 to 0x2CF
// BSStringT, BSString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG's BSStringT<char, N, Allocator> (and its BSString alias) reduced to the members the code needs
// BSStringT::c_str: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG returns the data pointer, or the empty string when it is null
// BSStringT::EMPTY: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG defines it in the class, here an external constant at RVA 0x1b58020 bound by hint
// BSStringT::Set: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence) OBSERVED; name only, the callee at RVA 0x10d710 (NG's set_cstr)
// BSStringT::_data, ::_size, ::_capacity: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED
// BSStringT::pad0C: GUESS(low); fills the 0x10 size
#pragma once

#include <cstdint>

#include "TESForm.h"

class BSStringT {
public:
    static const char EMPTY[1];

    const char* c_str() const { return _data ? _data : EMPTY; }
    bool        Set(const char* a_str, std::uint32_t a_len = 0);

    char*         _data;      // 00
    std::uint16_t _size;      // 08
    std::uint16_t _capacity;  // 0A
    std::uint32_t pad0C;      // 0C
};
using BSString = BSStringT;
static_assert(sizeof(BSStringT) == 0x10, "layout");

class TESImageSpaceModifier : public TESForm {
public:
    TESImageSpaceModifier();
    ~TESImageSpaceModifier() override;  // 00

    const char* GetFormEditorID() const override;             // 32
    bool        SetFormEditorID(const char* a_str) override;  // 33

    std::uint8_t unk20[0x2B0];  // 20
    BSString     formEditorID;  // 2D0
};
static_assert(sizeof(TESImageSpaceModifier) == 0x2E0, "layout");
