// TESFile type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG
// b93280e832f263dbef44e44cbe2936622a02f91a (MIT): include/RE/T/TESFile.h. No NG code is copied.
// TESFile, TESFile::OpenTES, ::Seek, ::SeekNextSubrecord, ::GetFormType, ::GetCurrentSubRecordType,
// ::Duplicate: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESFile::threadSafeParent, ::file, ::fileName, ::path, ::currentform, ::currentchunkID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESFile::actualChunkSize, ::filesize, ::fileOffset, ::formoffset, ::chunkoffset: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESFile::decompressedFormBuffer, ::decompressedFormBufferSize, ::lastError: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESFile::pad004, ::threadSafeFileMap, ::unk020, ::unk028, ::lockedFile, ::currRefOffset, ::pad4AC: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG declares unk020 as a 64-bit word (its upper half is unk024 here) and lockedFile as BSFile*
// TESFile::pad02A: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); NG splits the bytes 0x2A to 0x2F into pad02A and pad02C, merged here into one array
// TESFile::unk018, ::unk029: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); 0x29 is
// read as the flag that selects unk018 over file, 0x18 as a handle whose word at 0x24 is a position
// FORM, NiFile, Main: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the
// members and enumerators the compiled code needs; the object layouts are not claimed.
// FORM::form, ::length, ::flags, ::formID, ::versionControl, ::formVersion, ::vcVersion: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Main::threadID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); compared with the current thread id
// Main::singleton: GUESS; global pointer at RVA 0x3230530, which NG reads through Main::GetSingleton (RE::Offset::Main::Singleton).
// TESFile::unk024: GUESS(low); the word at 0x24 is used as the file position while unk018 is set
// BSFile: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the two position members
// BSFile::auxTrueFilePos, ::trueFilePos: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares auxTrueFilePos as std::int32_t, read here as an unsigned position
// TESFile::OpenInternal, ::ReadFormHeader, ::ReadChunkHeader, ::SeekRaw, ::DuplicateForThread: GUESS; callees at RVAs 0x1ca490, 0x1cf0f0, 0x1cf2e0, 0x1cfcf0, 0x1cf680 with no community name
// TESFile::EnsureOpen, ::IsCompressed, ::GetRootFile, ::QueryFilePosition: GUESS; inline helpers with no address of their own, named for what they do
// ConvertFormType: GUESS; the callee at RVA 0x1e5c10 maps a form record type to a FormType
// FormType: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only None is named
// g_tes4RecordType, g_seekOrigin, g_threadSafeFiles: GUESS; globals at RVAs 0x2078250, 0x1a41400,
// 0x2077fe8
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

class Main {
public:
    static Main* singleton;

    std::uint8_t  unk00[0x28];
    std::uint32_t threadID;  // 28
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

class BSFile {
public:
    std::uint8_t  unk00[0x58];
    std::uint32_t auxTrueFilePos;  // 58
    std::uint8_t  unk05C[0x170 - 0x5C];
    std::uint32_t trueFilePos;  // 170
};

class TESFile {
public:
    bool     OpenTES(NiFile::OpenMode a_accessMode, bool a_lock);
    bool     Seek(std::uint32_t a_offset);
    bool     SeekNextSubrecord();
    FormType GetFormType();
    std::uint32_t GetCurrentSubRecordType();
    TESFile* Duplicate(std::uint32_t a_cacheSize = 0x4000);

private:
    bool     OpenInternal(char* a_path, char* a_fileName, NiFile::OpenMode a_mode, bool a_lock);
    bool     ReadFormHeader();
    bool     ReadChunkHeader();
    void     SeekRaw(std::uint32_t a_offset, std::uint32_t a_origin);
    TESFile* DuplicateForThread(std::uint32_t a_threadID, std::uint32_t a_cacheSize);

    // Whether the current record's data is stored compressed (the file header record never is).
    bool IsCompressed() const;
    // Opens the file on demand, so every reader can assume a live handle.
    void EnsureOpen();
    // The outermost file of the thread-safe parent chain that starts at a_file (null for none).
    static TESFile* GetRootFile(TESFile* a_file);
    // The position the underlying file reports; the open-handle source depends on the access mode.
    std::uint32_t QueryFilePosition();

    std::uint32_t lastError;            // 000
    std::uint32_t pad004;               // 004
    TESFile*      threadSafeParent;     // 008
    void*         threadSafeFileMap;    // 010
    void*         unk018;               // 018
    std::uint32_t unk020;               // 020
    std::uint32_t unk024;               // 024
    std::uint8_t  unk028;               // 028
    std::uint8_t  unk029;               // 029
    std::uint8_t  pad02A[0x30 - 0x2A];  // 02A
    void*         lockedFile;           // 030
    BSFile*       file;                 // 038
    std::uint8_t  unk040[0x58 - 0x40];  // 040
    char          fileName[260];        // 058
    char          path[260];            // 15C
    std::uint8_t  unk260[0x280 - 0x260];  // 260
    std::uint32_t currRefOffset;        // 280
    FORM          currentform;          // 284
    std::uint32_t currentchunkID;       // 29C
    std::uint32_t actualChunkSize;      // 2A0
    std::uint32_t filesize;             // 2A4
    std::uint32_t fileOffset;           // 2A8
    std::uint32_t formoffset;           // 2AC
    std::uint32_t chunkoffset;          // 2B0
    std::uint8_t  unk2B4[0x4A0 - 0x2B4];  // 2B4
    char*         decompressedFormBuffer;      // 4A0
    std::uint32_t decompressedFormBufferSize;  // 4A8
    std::uint32_t pad4AC;                      // 4AC
};

static_assert(sizeof(FORM) == 0x18, "FORM size");
