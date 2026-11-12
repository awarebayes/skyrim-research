// BSReadWriteLock::UnlockForRead, UnlockForWrite, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0xce3510, 5 bytes (UnlockForRead); RVA 0xce3520, 26 bytes (UnlockForWrite).
// Evidence: findings/third-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with the class layout from the header beside this file.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. Both functions are compared.
// LockForRead (0xce3250) and LockForWrite (0xce32d0) are not part of this unit: their code
// matches except for callee-saved register assignment, which changes the unwind info.
#include "BSReadWriteLock.h"

#include <intrin.h>

void BSReadWriteLock::UnlockForRead()
{
    // atomic: readers release concurrently
    _InterlockedDecrement(reinterpret_cast<volatile long*>(&_lock));
}

void BSReadWriteLock::UnlockForWrite()
{
    if (_lock == (kLockWrite | 1)) {
        _writerThread = 0;
        // fence: clear the owner before the lock word is released
        _mm_mfence();
        // atomic: release the lock word
        _InterlockedExchange(reinterpret_cast<volatile long*>(&_lock), 0);
    } else {
        // atomic: drop one recursion level
        _InterlockedDecrement(reinterpret_cast<volatile long*>(&_lock));
    }
}
