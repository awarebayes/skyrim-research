// BGSCameraPath type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT). TESForm comes from
// the shared header; only the members and slots the compared code needs are declared here.
// Bodies adapted from community sources: none; tools/check_origin.py reports none above its
// threshold at the pinned checkouts.
// BGSCameraPath, BGSCameraPath::InitializeData, ::~BGSCameraPath, ::conditions, ::shots, ::data, ::pad39, ::pad3A, ::pad3C, ::childPaths, ::parentPath, ::prevPath: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESCondition: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); one pointer, size 0x8
// TESCondition::head: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares TESConditionItem*, an untyped pointer here
// BSSimpleList: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque 0x10 bytes (item and next)
// BSSimpleList::unk00: GUESS(low); opaque bytes
// NiFormArray: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); opaque, only used by pointer
// BGSCameraPath::BGSCameraPath: SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence); name only, defined only so the unit emits the vftable and the deleting destructor
// BGSCameraPath::~BGSCameraPath: declared and not defined so that the deleting destructor calls the plain one; bound by hint to 0x315f30
#pragma once

#include <cstdint>

#include "TESForm.h"

class NiFormArray;

struct TESCondition {
    void* head;  // 00
};

struct BSSimpleList {
    std::uint8_t unk00[0x10];  // 00
};

class BGSCameraPath : public TESForm {
public:
    BGSCameraPath();
    ~BGSCameraPath() override;  // 00

    void InitializeData() override;  // 04

    TESCondition   conditions;  // 20
    BSSimpleList   shots;       // 28
    std::uint8_t   data;        // 38
    std::uint8_t   pad39;       // 39
    std::uint16_t  pad3A;       // 3A
    std::uint32_t  pad3C;       // 3C
    NiFormArray*   childPaths;  // 40
    BGSCameraPath* parentPath;  // 48
    BGSCameraPath* prevPath;    // 50
};
static_assert(sizeof(BGSCameraPath) == 0x58, "layout");
