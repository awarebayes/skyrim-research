// BSShaderMaterial declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s19-bsshadermaterial-bsshadermaterial
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// BSShaderMaterial: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BSShaderMaterial::CopyMembers, BSShaderMaterial::~BSShaderMaterial: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// RawAt, BSShaderPair: GUESS(low)
// unknown08, unknown2C: GUESS(low)
#pragma once

#include <cstddef>
#include <cstdint>

template <class T>
T& RawAt(const void* a_base, std::ptrdiff_t a_offset)
{
    return *reinterpret_cast<T*>(const_cast<std::uint8_t*>(reinterpret_cast<const std::uint8_t*>(a_base)) + a_offset);
}

struct BSShaderPair
{
    float first;   // 00
    float second;  // 04
};

class BSShaderMaterial
{
public:
    BSShaderMaterial();
    virtual void CopyMembers(BSShaderMaterial* a_other);  // compared: 0x1575700
    virtual ~BSShaderMaterial() {}  // compared: 0x15758f0 (scalar deleting destructor)

    std::uint8_t unknown08[0x30];  // 08
};
static_assert(sizeof(BSShaderMaterial) == 0x38, "BSShaderMaterial size");
