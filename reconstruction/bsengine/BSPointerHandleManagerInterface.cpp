// BSPointerHandleManagerInterface<Actor>::GetHandle, build sse-steam-1-7-104.
//
// RVA 0x240f50, 54 bytes.
// Evidence: findings/second-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from a local listing of the pinned image
// with types from the header beside this file.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone, /Gy required).
// Only GetHandle is compared. A byte match shows this source and recipe produce the checked code;
// it does not verify the community name or that the original source looked like this.
#include "BSPointerHandleManagerInterface.h"

template <class T, class Manager>
BSPointerHandle<T> BSPointerHandleManagerInterface<T, Manager>::GetHandle(T* a_ptr)
{
    BSPointerHandle<T> handle;
    if (a_ptr && (a_ptr->flags & 0x3ff) == 0) {
        handle.native_handle = kNullHandle;
    } else {
        CreateRefHandle(handle, a_ptr);
    }
    return handle;
}

// Explicit instantiation so the member is emitted as an external symbol in this unit.
template class BSPointerHandleManagerInterface<Actor, BSPointerHandleManager>;
