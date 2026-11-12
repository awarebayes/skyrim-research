// TESFile type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG
// b93280e832f263dbef44e44cbe2936622a02f91a (MIT): include/RE/T/TESFile.h. No NG code is copied.
// TESFile, TESFile::OpenTES, ::GetFormType, ::GetCurrentSubRecordType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESFile::fileName, ::path, ::currentform, ::currentchunkID, ::actualChunkSize: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// NiFile, FORM, FormType: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the
// members and enumerators the compiled code needs; the object layouts are not claimed.
// FORM::form, ::length, ::flags, ::formID, ::versionControl, ::formVersion, ::vcVersion: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESFile::OpenInternal, ::ReadFormHeader, ::ReadChunkHeader: GUESS; callees at RVAs 0x1ca490,
// 0x1cf0f0, 0x1cf2e0 with no community name
// ConvertFormType: GUESS; the callee at RVA 0x1e5c10 maps a form record type to a FormType
// TESFile::unk000: GUESS(low); the leading members are not needed by the compared code
#pragma once

#include <cstdint>

class NiFile {
public:
    enum class OpenMode {
        kReadOnly = 0,
        kWriteOnly = 1,
        kAppendOnly = 2
    };
};

enum class FormType : std::uint32_t {
    None = 0
};

struct FORM {
    std::uint32_t form;             // 00
    std::uint32_t length;           // 04
    std::uint32_t flags;            // 08
    std::uint32_t formID;           // 0C
    std::uint32_t versionControl;   // 10
    std::uint16_t formVersion;      // 14
    std::uint16_t vcVersion;        // 16
};

class TESFile {
public:
    bool          OpenTES(NiFile::OpenMode a_accessMode, bool a_lock);
    FormType      GetFormType();
    std::uint32_t GetCurrentSubRecordType();

private:
    bool OpenInternal(char* a_path, char* a_fileName, NiFile::OpenMode a_mode, bool a_lock);
    bool ReadFormHeader();
    bool ReadChunkHeader();

    std::uint8_t  unk000[0x58];            // 000
    char          fileName[260];           // 058
    char          path[260];               // 15C
    std::uint8_t  unk260[0x284 - 0x260];   // 260
    FORM          currentform;             // 284
    std::uint32_t currentchunkID;          // 29C
    std::uint32_t actualChunkSize;         // 2A0
};

static_assert(sizeof(FORM) == 0x18, "FORM size");
