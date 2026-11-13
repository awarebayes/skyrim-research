// NiBinaryStream functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s05-nibinarystream-nibinarystream
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-small-2-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by luna56-medium-n1 (the model or person who writes the bodies), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xeae190, 17 bytes: NiBinaryStream::get_info
//   RVA 0xeae130, 27 bytes: NiBinaryStream::ctor
// Adapted bodies: none.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiBinaryStream.h"

void NiBinaryStream::get_info(BufferInfo& a_buf)
{
    a_buf.data = 0;
    a_buf.size = 0;
    a_buf.capacity = 0;
    a_buf.flags = 0;
}

NiBinaryStream::NiBinaryStream()
{
    unknown10 = 0;
    unknown18 = 0;
    unknown08 = 0;
}
