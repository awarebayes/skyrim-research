// BSAnimationGraphChannel declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-n-bsanimationgraphchannel
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// BSAnimationGraphChannel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSAnimationGraphChannel::~BSAnimationGraphChannel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSAnimationGraphChannelMember: GUESS(low); stand-in, the out-of-line destructor is bound by hint to RVA 0xEB1100
// unk08, unk00: GUESS(low)
#pragma once

#include <cstdint>
#include <cstddef>

class BSAnimationGraphChannelMember {
public:
    ~BSAnimationGraphChannelMember();
    std::uint64_t unk00;
    std::uint64_t unk08;
};

class BSAnimationGraphChannel {
public:
    BSAnimationGraphChannel();
    virtual ~BSAnimationGraphChannel();  // compared: 0x21f0c0 (scalar deleting destructor)

    std::uint64_t                unk08;
    BSAnimationGraphChannelMember member10;
};
static_assert(sizeof(BSAnimationGraphChannel) == 0x20, "BSAnimationGraphChannel size");
