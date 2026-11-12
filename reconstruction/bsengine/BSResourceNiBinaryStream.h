// BSResourceNiBinaryStream type declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Class, member and virtual names follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT)
// include/RE/B/BSResourceNiBinaryStream.h and include/RE/N/NiBinaryStream.h; layout sizes and
// offsets are from the image.
// Stand-ins: NiBinaryStream, BufferInfo, BSResource::Stream, StreamBuffer are
// declared here with only the members and slots the compared code needs.
// Adapted bodies: none declared; tools/check_origin.py reports none above its threshold at
// CommonLibSSE-NG b93280e, powerof3/CommonLibSSE 654e55f and momusdigital/fnv_decomp 91e1b6e8.
// NiBinaryStream, BufferInfo: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiBinaryStream: EXE_RTTI
// good, seek, tell, get_info, set_endian_swap, _absoluteCurrentPos, _readFn, _writeFn: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// buffer, totalSize, bufferAllocSize, bufferReadSize, bufferPos, streamPos, pad1C: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSResourceNiBinaryStream: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// stream, buffer, streamPos, lastError: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// SetEndianSwap: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG names the slot set_endian_swap
// Stream, StreamBuffer: STANDIN GUESS(low); BSResource::Stream is the NG name of the pointee, its members are unnamed here
// refCount, flags, owner, data, begin, limit, position: GUESS(low)
#pragma once

#include <cstdint>

// BufferInfo: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
struct BufferInfo
{
	void*         buffer;           // 00
	std::uint32_t totalSize;        // 08
	std::uint32_t bufferAllocSize;  // 0C
	std::uint32_t bufferReadSize;   // 10
	std::uint32_t bufferPos;        // 14
	std::uint32_t streamPos;        // 18
	std::uint32_t pad1C;            // 1C
};
static_assert(sizeof(BufferInfo) == 0x20, "BufferInfo size");

class NiBinaryStream
{
public:
	using ReadFn = std::uint32_t(NiBinaryStream* a_this, void* a_buffer, std::uint32_t a_bytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents);
	using WriteFn = std::uint32_t(NiBinaryStream* a_this, const void* a_buffer, std::uint32_t a_bytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents);

	NiBinaryStream();
	virtual ~NiBinaryStream();  // 00

	virtual bool          good() const = 0;                    // 01
	virtual void          seek(std::int32_t a_numBytes) = 0;   // 02
	virtual std::uint32_t tell() const;                        // 03
	virtual void          get_info(BufferInfo& a_buf);         // 04
	virtual void          set_endian_swap(bool a_doSwap) = 0;  // 05

	std::uint32_t _absoluteCurrentPos;  // 08
	std::uint32_t _pad0C;               // 0C
	ReadFn*       _readFn;              // 10
	WriteFn*      _writeFn;             // 18
};
static_assert(sizeof(NiBinaryStream) == 0x20, "NiBinaryStream size");

// WrittenCount: GUESS(low); the byte count the stream write reports back, with an empty destructor
struct WrittenCount
{
	std::uint64_t value;
	WrittenCount() : value(0) {}
	~WrittenCount() {}
};

namespace BSResource
{
	class Stream
	{
	public:
		virtual ~Stream();            // 00
		virtual void Unk_01();        // 01
		virtual void Unk_02();        // 02
		virtual void Unk_03();        // 03
		virtual void Unk_04();        // 04
		virtual void Unk_05();        // 05
		virtual void Unk_06();        // 06
		virtual void Unk_07(void* a_data, std::uint64_t a_size, WrittenCount* a_out);  // 07

		std::uint32_t totalSize;  // 08
		std::uint32_t pad0C;      // 0C
		std::uint32_t refCount;   // 10
	};
}

// ReadNoSwap, ReadSwap, WriteNoSwap, WriteSwap: GUESS(low); the per-endianness stream functions, bound by RVA hints
std::uint32_t ReadNoSwap(NiBinaryStream* a_this, void* a_buffer, std::uint32_t a_bytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents);
std::uint32_t ReadSwap(NiBinaryStream* a_this, void* a_buffer, std::uint32_t a_bytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents);
std::uint32_t WriteNoSwap(NiBinaryStream* a_this, const void* a_buffer, std::uint32_t a_bytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents);
std::uint32_t WriteSwap(NiBinaryStream* a_this, const void* a_buffer, std::uint32_t a_bytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents);

class StreamBuffer
{
public:
	BSResource::Stream* owner;     // 00
	std::uint64_t       begin;     // 08
	std::uint64_t       limit;     // 10
	std::uint64_t       position;  // 18
	std::uint64_t       unk20;     // 20
	void*               data;      // 28
	std::uint32_t       flags;     // 30

	// FillInfo: GUESS(low); callee of get_info
	void FillInfo(BufferInfo* a_info, std::uint32_t* a_readSize, std::uint64_t a_posAndError);
};

class BSResourceNiBinaryStream : public NiBinaryStream
{
public:
	BSResourceNiBinaryStream();
	~BSResourceNiBinaryStream() override;  // 00

	bool          good() const override;                    // 01
	void          seek(std::int32_t a_numBytes) override;   // 02
	std::uint32_t tell() const override;                    // 03
	void          get_info(BufferInfo& a_buf) override;     // 04
	void          set_endian_swap(bool a_doSwap) override;  // 05

	BSResource::Stream* stream;     // 20
	StreamBuffer*       buffer;     // 28
	std::uint32_t       streamPos;  // 30
	std::uint32_t       lastError;  // 34
};
static_assert(sizeof(BSResourceNiBinaryStream) == 0x38, "BSResourceNiBinaryStream size");
