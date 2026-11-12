// BGSMovableStatic::InitializeData and the destructor adjustor thunk, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x264444, 9 bytes (dtor, the vtable thunk of the secondary base at +0x10 into the deleting destructor);
// RVA 0x2640a0, 12 bytes (InitializeData).
// Evidence: findings/fifth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image. Names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT).
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// The destructor is empty: the compiler emits the deleting destructor and its adjustor thunks
// beside the vftables.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The two functions above are compared.
#include "BGSMovableStatic.h"

// The constructor is not compared: it is defined so that this unit emits the vftables and with
// them the destructor thunks. Its body is a minimal stand-in.
BGSMovableStatic::BGSMovableStatic()
{
}

BGSMovableStatic::~BGSMovableStatic()
{
}

void BGSMovableStatic::InitializeData()
{
    soundLoop = nullptr;
}
