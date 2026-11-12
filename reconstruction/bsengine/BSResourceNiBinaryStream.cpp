// BSResourceNiBinaryStream: tell, good, SetEndianSwap, deleting destructor, get_info.
// Build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0xf01650, 4 bytes: BSResourceNiBinaryStream::tell
// RVA 0xf01600, 9 bytes: BSResourceNiBinaryStream::good
// RVA 0xf016e0, 47 bytes: BSResourceNiBinaryStream::SetEndianSwap
// RVA 0xf01be0, 52 bytes: BSResourceNiBinaryStream::~BSResourceNiBinaryStream (scalar deleting destructor)
// RVA 0xf01660, 115 bytes: BSResourceNiBinaryStream::get_info
// RVA 0xf014c0 (the plain destructor body the deleting destructor calls) is not defined here; it is out of line
//
// Evidence: findings/fourth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with names from CommonLibSSE-NG b93280e (MIT).
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json; five functions are compared.
// Bodies adapted from community sources are listed above; tools/check_origin.py reports none
// other above its threshold at the pinned checkouts.
#include "BSResourceNiBinaryStream.h"

BSResourceNiBinaryStream::BSResourceNiBinaryStream()
{
	stream = nullptr;
	buffer = nullptr;
	streamPos = 0;
	lastError = 0;
}

bool BSResourceNiBinaryStream::good() const
{
	return stream != nullptr;
}

std::uint32_t BSResourceNiBinaryStream::tell() const
{
	return streamPos;
}

void BSResourceNiBinaryStream::set_endian_swap(bool a_doSwap)
{
	if (a_doSwap) {
		_readFn = ReadSwap;
		_writeFn = WriteSwap;
	} else {
		_readFn = ReadNoSwap;
		_writeFn = WriteNoSwap;
	}
}

void BSResourceNiBinaryStream::get_info(BufferInfo& a_buf)
{
	a_buf.buffer = nullptr;
	a_buf.totalSize = stream ? stream->totalSize : 0;
	if (buffer) {
		// FillInfo: GUESS(low) OBSERVED; the call passes streamPos and lastError together as one 8-byte value
		buffer->FillInfo(&a_buf, &a_buf.bufferReadSize, *reinterpret_cast<const std::uint64_t*>(&streamPos));
		a_buf.bufferAllocSize = a_buf.bufferReadSize;
		buffer->flags &= ~1u;
	} else {
		a_buf.bufferAllocSize = 0;
		a_buf.bufferReadSize = 0;
		a_buf.bufferPos = 0;
	}
	a_buf.streamPos = streamPos;
}
