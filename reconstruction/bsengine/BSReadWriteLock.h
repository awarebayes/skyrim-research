// BSReadWriteLock type declaration, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG
// b93280e832f263dbef44e44cbe2936622a02f91a (MIT): include/RE/B/BSAtomic.h. No NG code is copied.
// BSReadWriteLock, BSReadWriteLock::_writerThread, ::_lock, ::UnlockForRead, ::UnlockForWrite: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSReadWriteLock::kLockWrite, ::kLockCountMask: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>

class BSReadWriteLock {
public:
    enum : std::uint32_t {
        kLockWrite = 0x80000000,
        kLockCountMask = 0xFFFFFFF
    };

    void UnlockForRead();
    void UnlockForWrite();

private:
    // Community declares both volatile. The owner word is plain here: it is only written under
    // the lock and compared against the current thread id, so no reload semantics are needed.
    std::uint32_t _writerThread;  // 00
    volatile std::uint32_t _lock; // 04
};
