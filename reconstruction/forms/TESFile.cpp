// TESFile::OpenTES, GetCurrentSubRecordType, GetFormType, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x1ca460, 36 bytes (OpenTES); RVA 0x1cdc10, 47 bytes (GetCurrentSubRecordType);
// RVA 0x1cd7d0, 72 bytes (GetFormType).
// Evidence: findings/third-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with the class layout from the header beside this file.
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community method names or that the original source looked like this.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The three functions above are compared.
#include "TESFile.h"

FormType ConvertFormType(std::uint32_t a_recordType);

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
