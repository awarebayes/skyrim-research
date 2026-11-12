// Type declarations for the BSPointerHandleManagerInterface translation unit (build sse-steam-1-7-104).
//
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names follow CharmedBaryon/CommonLibSSE-NG b93280e832f263dbef44e44cbe2936622a02f91a (MIT):
// include/RE/B/BSPointerHandle.h; these are minimal stand-ins.
// Adapted bodies: none declared; tools/check_origin.py reports none above its threshold (0.75)
// at CommonLibSSE-NG b93280e, powerof3/CommonLibSSE 654e55f and momusdigital/fnv_decomp 91e1b6e8.
// The BSPointerHandle constructor's one-statement body necessarily coincides with NG's.
//   BSPointerHandleManagerInterface, GetHandle, BSPointerHandle   COMMUNITY (unverified)
//   CreateRefHandle   COMMUNITY (NG include/RE/Offsets.h, a free function id); parameter types GUESS
//   kNullHandle       GUESS: a 32-bit global in .data, no community name; the value stored when the
//                     object is non-null and its flag bits are clear. Its meaning is not established.
//   Actor::flags      GUESS: the 32-bit word at offset 0x28 tested against mask 0x3ff.
// The template is instantiated for Actor with a placeholder Manager type.
#pragma once

#include <cstdint>

template <class T>
struct BSPointerHandle {
    // User-provided special members make the type non-trivially copyable, so it is returned
    // through a hidden pointer as in the image (NG declares comparable constructors).
    BSPointerHandle() = default;
    BSPointerHandle(const BSPointerHandle& a_rhs) : native_handle(a_rhs.native_handle) {}

    std::uint32_t native_handle;  // left uninitialised by the default constructor
};

class Actor {
public:
    std::uint8_t  unk00[0x28];
    std::uint32_t flags;  // 0x28
};

struct BSPointerHandleManager;

extern std::uint32_t kNullHandle;

void CreateRefHandle(BSPointerHandle<Actor>& a_out, Actor* a_ptr);

template <class T, class Manager>
class BSPointerHandleManagerInterface {
public:
    using value_type = T;

    static BSPointerHandle<T> GetHandle(T* a_ptr);
};
