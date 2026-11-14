// TESWorldSpace member functions, build sse-steam-1-7-104.
//
// Labels: v2
// RVA 0x30b710, 22 bytes (GetFormEditorID);
// RVA 0x314930, 52 bytes (~TESWorldSpace, the deleting destructor);
// RVA 0x30e8d0, 129 bytes (GetCellByPosition); RVA 0x30d050, 136 bytes (FindInFileFast).
// Evidence: findings/fourth-batch-selection.md.
// Source exposure: mixed. Drafted by claude-sonnet-5-5 from local instruction listings of the
// pinned image, with the class layout from the header beside this file. Names are from
// CharmedBaryon/CommonLibSSE-NG b93280e (MIT), and GetCellByPosition's from meh321/AddressLibraryDatabase 0379cb6. A byte match shows that this source and recipe produce the checked code; it
// does not verify the community method names or that the original source looked like this.
// The plain destructor and the base constructors are declared, not defined, in this unit.
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json. The functions above are compared.
#include "TESWorldSpace.h"

extern std::uint8_t kRecordFormType;

// The constructor is not compared: it is defined so that this unit emits the vftable and with
// it the deleting destructor, as the original unit did. Its body is a minimal stand-in.
TESWorldSpace::TESWorldSpace()
{
}

const char* TESWorldSpace::GetFormEditorID() const
{
    return editorID.c_str();
}

bool TESWorldSpace::IsParentForm()
{
    return true;
}

bool TESWorldSpace::FindInFileFast(TESFile* a_mod)
{
    OffsetData* offsetData = GetOffsetData();
    if (!a_mod || !a_mod->IsRecordFileLoaded() || !offsetData || offsetData->fileOffset == 0) {
        return false;
    }
    if (!a_mod->Seek(offsetData->fileOffset)) {
        return false;
    }
    return static_cast<std::uint32_t>(a_mod->GetFormType()) == kRecordFormType && a_mod->currentFormID == formID;
}

TESObjectCELL* TESWorldSpace::GetCellByPosition(const NiPoint3& a_pos) const
{
    const std::int32_t cellX = FloorToCell(a_pos.x);
    const std::int32_t cellY = FloorToCell(a_pos.y);
    if (cellX > 0x7FFF || cellY > 0x7FFF || cellX < -0x8000 || cellY < -0x8000) {
        return nullptr;
    }
    return CellAtCoordinates(cellX, cellY);
}
