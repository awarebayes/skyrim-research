// BGSLoadGameBuffer accessors, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x637a90, 12 bytes (GetVersion); RVA 0x637e70, 51 bytes (LoadDataEndian);
// RVA 0x637ab0, 110 bytes (ReadFormID).
// Evidence: findings/fourth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image and the class layout in the header beside this file. A byte match shows that this
// source and recipe produce the checked code; it does not verify the community names.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The three functions above are compared.
#include "BGSLoadGameBuffer.h"

#include <cstring>
#include <cstdint>

std::uint8_t BGSLoadGameBuffer::GetVersion()
{
	return gBGSSaveLoadGame->QueryState();
}

void BGSLoadGameBuffer::LoadDataEndian(void* a_data, std::uint32_t a_size)
{
	std::memcpy(a_data, static_cast<std::uint8_t*>(buffer) + bufferPosition, a_size);
	bufferPosition += a_size;
}

bool BGSLoadGameBuffer::ReadFormID(std::uint32_t& a_formID)
{
	BGSNumericIDIndex index;
	const std::uint32_t position = bufferPosition;
	const std::uint8_t* src = static_cast<const std::uint8_t*>(buffer) + position;
	// the index is read as a 16-bit pair then a byte, which is how the target copies its 3 bytes
	std::memcpy(&index, src, 2);
	std::memcpy(&index.data3, src + 2, 1);
	bufferPosition = position + 3;
	a_formID = index.GetNumericID();
	const bool empty = index.data1 == 0 && index.data2 == 0 && index.data3 == 0;
	return !empty && a_formID == 0;
}
