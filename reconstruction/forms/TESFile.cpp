// TESFile::OpenTES, GetCurrentSubRecordType, GetFormType, SeekNextSubrecord, Duplicate, Seek,
// build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x1ca460, 36 bytes (OpenTES); RVA 0x1cdc10, 47 bytes (GetCurrentSubRecordType);
// RVA 0x1cd7d0, 72 bytes (GetFormType); RVA 0x1cdc60, 167 bytes (SeekNextSubrecord);
// RVA 0x1ce7e0, 188 bytes (Duplicate); RVA 0x1cd860, 409 bytes (Seek).
// Evidence: findings/third-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with the class layout from the header beside this file. SeekNextSubrecord,
// Duplicate and Seek were finished by claude-opus-5-5 from the Drafter's near-misses.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. All six functions are compared.
// GetCurrentThreadId, GetLastError, FormatMessageA, LocalFree: STANDIN OBSERVED; Win32 imports of the image, declared locally
#include "TESFile.h"

#include <cstring>

extern "C" __declspec(dllimport) unsigned long __stdcall GetCurrentThreadId();
extern "C" __declspec(dllimport) unsigned long __stdcall GetLastError();
extern "C" __declspec(dllimport) unsigned long __stdcall FormatMessageA(unsigned long a_flags,
    const void* a_source, unsigned long a_messageId, unsigned long a_languageId, char* a_buffer,
    unsigned long a_size, void* a_arguments);
extern "C" __declspec(dllimport) void* __stdcall LocalFree(void* a_mem);

extern bool                 g_threadSafeFiles;
extern std::uint32_t        g_tes4RecordType;
extern const std::uint32_t  g_seekOrigin;
FormType                    ConvertFormType(std::uint32_t a_recordType);
Main*                       Main::singleton;

namespace {
    const std::uint32_t kCompressedFlag = 0x00040000;
}

void TESFile::EnsureOpen()
{
    if (!g_threadSafeFiles || !unk029) {
        if (file) {
            return;
        }
    } else if (unk018) {
        return;
    }
    OpenTES(NiFile::OpenMode::kReadOnly, false);
}

bool TESFile::OpenTES(NiFile::OpenMode a_accessMode, bool a_lock)
{
    return OpenInternal(path, fileName, a_accessMode, a_lock);
}

std::uint32_t TESFile::GetCurrentSubRecordType()
{
    if (currentchunkID == 0 && !ReadChunkHeader()) {
        return 0;
    }
    return currentchunkID;
}

FormType TESFile::GetFormType()
{
    if (currentform.form == 0) {
        if (!ReadFormHeader()) {
            return FormType::None;
        }
        currentchunkID = 0;
        actualChunkSize = 0;
        ReadChunkHeader();
    }
    return ConvertFormType(currentform.form);
}

bool TESFile::IsCompressed() const
{
    return currentform.form != g_tes4RecordType && (currentform.flags & kCompressedFlag) != 0;
}

bool TESFile::SeekNextSubrecord()
{
    std::uint32_t limit = currentform.length;
    if (IsCompressed()) {
        limit = decompressedFormBufferSize;
    }
    formoffset += actualChunkSize + 6;
    if (formoffset >= limit) {
        currentchunkID  = 0;
        actualChunkSize = 0;
        return false;
    }
    // a compressed record is read from the decompressed buffer, so only plain records seek the file
    const std::uint32_t position = fileOffset + formoffset + sizeof(FORM);
    if (!IsCompressed()) {
        SeekRaw(position, g_seekOrigin);
    }
    chunkoffset     = 0;
    currentchunkID  = 0;
    actualChunkSize = 0;
    ReadChunkHeader();
    return true;
}

TESFile* TESFile::GetRootFile(TESFile* a_file)
{
    while (a_file && a_file->threadSafeParent) {
        a_file = a_file->threadSafeParent;
    }
    return a_file;
}

TESFile* TESFile::Duplicate(std::uint32_t a_cacheSize)
{
    EnsureOpen();
    TESFile* root = this;
    while (GetRootFile(root->threadSafeParent)) {
        root = GetRootFile(root->threadSafeParent);
    }
    if (GetCurrentThreadId() == Main::singleton->threadID) {
        return root;
    }
    return root->DuplicateForThread(GetCurrentThreadId(), a_cacheSize);
}

std::uint32_t TESFile::QueryFilePosition()
{
    if (g_threadSafeFiles && unk029) {
        if (!unk018) {
            return 0;
        }
        return unk024;
    }
    if (!file) {
        return 0;
    }
    std::uint32_t position = file->auxTrueFilePos;
    if (position == 0xFFFFFFFF) {
        position = file->trueFilePos;
    }
    return position;
}

bool TESFile::Seek(std::uint32_t a_offset)
{
    EnsureOpen();
    if (decompressedFormBuffer) {
        decompressedFormBuffer     = nullptr;
        decompressedFormBufferSize = 0;
    }
    fileOffset = a_offset;
    if (a_offset >= filesize) {
        std::memset(&currentform, 0, sizeof(currentform));
        return false;
    }
    SeekRaw(a_offset, g_seekOrigin);
    fileOffset = QueryFilePosition();
    if (fileOffset == 0xFFFFFFFF) {
        // the failure text is formatted and released but never kept
        char* message;
        FormatMessageA(0x1300, nullptr, GetLastError(), 0x400, reinterpret_cast<char*>(&message), 0, nullptr);
        LocalFree(message);
        return false;
    }
    formoffset = 0;
    chunkoffset = 0;
    std::memset(&currentform, 0, sizeof(currentform));
    GetFormType();
    return true;
}
