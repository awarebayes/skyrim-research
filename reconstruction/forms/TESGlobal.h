// TESGlobal type declaration, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT): include/RE/T/TESGlobal.h and
// include/RE/B/BSString.h. Adapted bodies: none declared.
// TESGlobal, TESGlobal::GetFormEditorID, ::SetFormEditorID, ::formEditorID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSStringT, BSString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG's BSStringT<char, N, Allocator> (and its BSString alias) reduced to the members the code needs
// BSStringT::c_str: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG returns the data pointer, or the empty string when it is null
// BSStringT::EMPTY: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG defines it in the class, here an external constant at RVA 0x1b58020 bound by hint
// BSStringT::Set: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence) OBSERVED; name only, the callee at RVA 0x10d710 (NG's set_cstr)
// BSStringT::_data, ::_size, ::_capacity: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED
// BSStringT::pad0C: GUESS(low); fills the 0x10 size
// TESGlobal::unk30: GUESS(low); the type, padding and value members are not recovered
#pragma once

#include <cstdint>

#include "TESForm.h"

class BSStringT {
public:
    static const char EMPTY[1];

    const char* c_str() const { return _data ? _data : EMPTY; }
    bool        Set(const char* a_str, std::uint32_t a_len = 0);

    char*         _data;     // 00
    std::uint16_t _size;     // 08
    std::uint16_t _capacity; // 0A
    std::uint32_t pad0C;     // 0C
};
using BSString = BSStringT;
static_assert(sizeof(BSStringT) == 0x10, "layout");

class TESGlobal : public TESForm {
public:
    const char* GetFormEditorID() const override;             // 32
    bool        SetFormEditorID(const char* a_str) override;  // 33

    BSString      formEditorID;  // 20
    std::uint64_t unk30;         // 30
};
static_assert(sizeof(TESGlobal) == 0x38, "layout");
