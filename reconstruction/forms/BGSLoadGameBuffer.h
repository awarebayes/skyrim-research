// BGSLoadGameBuffer, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (community headers and local instruction listings of the pinned image).
// Layout and names are from CharmedBaryon/CommonLibSSE-NG b93280e (MIT), checked against the listings.
// Stand-ins: BGSNumericIDIndex (name and members from NG include/RE/B/BGSNumericIDIndex.h) and
// BGSSaveLoadGame (name from NG include/RE/B/BGSSaveLoadGame.h; only the singleton pointer and the
// one method GetVersion calls are declared).
// BGSLoadGameBuffer: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
#pragma once

#include <cstdint>

// BGSNumericIDIndex: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
struct BGSNumericIDIndex
{
	// data1, data2, data3: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	std::uint8_t data1 = 0;  // 0
	std::uint8_t data2 = 0;  // 1
	std::uint8_t data3 = 0;  // 2

	// GetNumericID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); target 0x632cc0
	std::uint32_t GetNumericID() const;
};

// BGSSaveLoadGame: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class BGSSaveLoadGame
{
public:
	// QueryState: GUESS(low); unnamed target 0x618230, returns a byte, called with the singleton
	std::uint8_t QueryState();
};

// gBGSSaveLoadGame: GUESS(low); the pointer NG reads in BGSSaveLoadGame::GetSingleton, data at 0x3223e18
extern BGSSaveLoadGame* gBGSSaveLoadGame;

// BGSLoadGameBuffer: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI; sizeof 0x28 read from the listings
class BGSLoadGameBuffer
{
public:
	// ~BGSLoadGameBuffer: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 0
	virtual ~BGSLoadGameBuffer();
	// GetVersion: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 1, target 0x637a90
	virtual std::uint8_t GetVersion();

	// LoadDataEndian: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares three parameters, the listing shows data and a byte count
	void LoadDataEndian(void* a_data, std::uint32_t a_size);
	// ReadFormID: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission) OBSERVED; reads a 3-byte index, writes the id, returns bool
	bool ReadFormID(std::uint32_t& a_formID);

	// buffer, bufferPosition: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	void*         buffer;          // 08
	std::uint64_t unk10;           // 10
	std::uint32_t unk18;           // 18
	std::uint32_t unk1C;           // 1C
	std::uint32_t unk20;           // 20
	std::uint32_t bufferPosition;  // 24
};
static_assert(sizeof(BGSLoadGameBuffer) == 0x28, "size");
