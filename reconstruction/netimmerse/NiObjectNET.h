// NiObjectNET declaration for build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names follow CharmedBaryon/CommonLibSSE-NG b93280e (MIT) include/RE/N/NiObjectNET.h,
// include/RE/N/NiStream.h, include/RE/N/NiBinaryStream.h, include/RE/N/NiExtraData.h and
// include/RE/N/NiTimeController.h. Members, slots and sizes were checked against the listings.
// Stand-ins declared here (not edited elsewhere): BSFixedString, NiPointer, NiBinaryStream,
// NiStream, NiExtraData, NiTimeController. NiObject comes from the shared NiObject.h.
// Adapted code: no body in this file is copied from a community source; the only inline body is
// the NiPointer assignment, which follows the usual smart-pointer shape and the listing.
// Bodies adapted from community sources are listed above (none); tools/check_origin.py reports
// none other above its threshold at the pinned checkouts.
// Vtable slot order and sizeof(NiObjectNET) == 0x30 come from the image RTTI and vftable.
// NiObjectNET: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
#pragma once

#include "NiObject.h"

#include <intrin.h>
#include <cstddef>
#include <cstdint>

class NiTimeController;
class NiExtraData;

// BSFixedString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); one pointer, as the zeroing store shows
class BSFixedString
{
public:
	// _data: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
	const char* _data{ nullptr };  // 00
};

// NiPointer: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the pointer and assignment
// pointer: GUESS(low); NG names the pointer differently
template <class T>
class NiPointer
{
public:
	NiPointer& operator=(T* a_object)
	{
		T* old = pointer;
		if (old != a_object) {
			if (a_object) {
				// hot path: reference counts are bumped atomically
				_InterlockedIncrement(reinterpret_cast<volatile long*>(&a_object->_refCount));
			}
			pointer = a_object;
			if (old) {
				// hot path: reference counts are dropped atomically
				if (_InterlockedDecrement(reinterpret_cast<volatile long*>(&old->_refCount)) == 0) {
					old->DeleteThis();
				}
			}
		}
		return *this;
	}

	T* pointer{ nullptr };  // 00
};

// NiBinaryStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the write path only
// _absoluteCurrentPos, _writeFn: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unk10: GUESS(low); the read function pointer is not used here
// WriteBytes: GUESS(low); NG's binary_write is a protected member, called here through the stream
class NiBinaryStream
{
public:
	using WriteFn = std::uint32_t(NiBinaryStream* a_this, const void* a_buffer, std::uint32_t a_bytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents);

	std::uint32_t WriteBytes(const void* a_buffer, std::uint32_t a_totalBytes, std::uint32_t* a_componentSizes, std::uint32_t a_numComponents = 1)
	{
		std::uint32_t written = _writeFn(this, a_buffer, a_totalBytes, a_componentSizes, a_numComponents);
		_absoluteCurrentPos += written;
		return written;
	}

	void*         vftable;               // 00
	std::uint32_t _absoluteCurrentPos;   // 08
	std::uint32_t _pad0C;                // 0C
	void*         unk10;                 // 10
	WriteFn*      _writeFn;              // 18
};

// NiStream: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slots 00 to 0C, oStr
// RegisterFixedString, SaveLinkID, oStr: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Unk_01 to Unk_06: GUESS(low); placeholders for NG's Load1 to Save3 so later slots line up
// Unk_07: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// unk08: GUESS(low); members before iStr are not recovered here
class NiStream
{
public:
	virtual ~NiStream();                                                // 00
	virtual void Unk_01();                                              // 01
	virtual void Unk_02();                                              // 02
	virtual void Unk_03();                                              // 03
	virtual void Unk_04();                                              // 04
	virtual void Unk_05();                                              // 05
	virtual void Unk_06();                                              // 06
	virtual void Unk_07();                                              // 07
	virtual bool RegisterFixedString(const BSFixedString& a_fixedString);  // 08
	virtual bool RegisterSaveObject(NiObject* a_object);                // 09
	virtual bool ChangeObject(NiObject* a_object);                      // 0A
	virtual std::uint32_t GetLinkIDFromObject(const NiObject* a_object);  // 0B
	virtual void SaveLinkID(const NiObject* a_object);                  // 0C

	std::uint8_t    unk08[0x290];  // 008
	NiBinaryStream* iStr;          // 298
	NiBinaryStream* oStr;          // 2A0
};
static_assert(offsetof(NiStream, oStr) == 0x2A0, "NiStream oStr");

// NiExtraData: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); IsStreamable at slot 25
class NiExtraData : public NiObject
{
public:
	virtual bool IsStreamable() const;  // 25
};

// NiTimeController: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); IsStreamable at slot 2D, next at 40
// Unk_25 to UnkSlot2B: GUESS(low); placeholders for NG's Start to ComputeScaledTime
// UnkSlot2C: GUESS(low); NG names this slot OnPreDisplay
// unk10: GUESS(low); members before next are not recovered here
class NiTimeController : public NiObject
{
public:
	virtual void Unk_25();  // 25
	virtual void Unk_26();  // 26
	virtual void Unk_27();  // 27
	virtual void Unk_28();  // 28
	virtual void Unk_29();  // 29
	virtual void Unk_2A();  // 2A
	virtual void UnkSlot2B();  // 2B
	virtual void UnkSlot2C();  // 2C
	virtual bool IsStreamable() const;  // 2D

	std::uint8_t                unk10[0x30];  // 10
	NiPointer<NiTimeController> next;         // 40
};
static_assert(sizeof(NiTimeController) == 0x48, "NiTimeController size");

// NiObjectNET: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// GetRTTI, LoadBinary, LinkObject, RegisterStreamables, SaveBinary, IsEqual, ProcessClone, PostLinkObject, AddExtraData, SetExtraDataSize, name, controllers, extra, extraDataSize, maxSize, pad2C: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiObjectNET : public NiObject
{
public:
	NiObjectNET();
	~NiObjectNET() override;  // 00

	const NiRTTI* GetRTTI() const override;                            // 02
	void          LoadBinary(NiStream& a_stream) override;             // 18
	void          LinkObject(NiStream& a_stream) override;             // 19
	bool          RegisterStreamables(NiStream& a_stream) override;    // 1A
	void          SaveBinary(NiStream& a_stream) override;             // 1B
	bool          IsEqual(NiObject* a_object) override;                // 1C
	void          ProcessClone(NiCloningProcess& a_cloning) override;  // 1D
	void          PostLinkObject(NiStream& a_stream) override;         // 1E

	bool AddExtraData(NiExtraData* a_extra);
	bool SetExtraDataSize(std::uint16_t a_size);

	BSFixedString               name;           // 10
	NiPointer<NiTimeController> controllers;    // 18
	NiExtraData**               extra;          // 20
	std::uint16_t               extraDataSize;  // 28
	std::uint16_t               maxSize;        // 2A
	std::uint32_t               pad2C;          // 2C
};
static_assert(sizeof(NiObjectNET) == 0x30, "NiObjectNET size");
