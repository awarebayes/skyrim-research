// Type declarations for the TESWorldSpace unit (build sse-steam-1-7-104).
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names follow CharmedBaryon/CommonLibSSE-NG b93280e832f263dbef44e44cbe2936622a02f91a (MIT)
// and the meh321/AddressLibraryDatabase 0379cb6 name list (used with the author's permission as
// reported by the maintainer).
// Adapted bodies: none declared; tools/check_origin.py reports none above its threshold (0.75)
// at CommonLibSSE-NG b93280e, powerof3/CommonLibSSE 654e55f and momusdigital/fnv_decomp 91e1b6e8.
// Every class other than TESWorldSpace is a minimal stand-in that declares only
// the members and virtual slots the compared code needs; the layouts of the stand-ins are not
// claimed to match the game. Unk_NN placeholders only keep the compared virtual slots at the
// vtable offsets the image encodes (slot NN is the byte offset NN * 8). Members without a name
// only keep the named members at the offsets the code reads.
// TESWorldSpace, IsFormTypeChild, GetFormEditorID, SetFormEditorID, FindInFileFast, ClearData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// editorID: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// GetCellByPosition: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); Address Library id 20504, no declaration in either community header
// BaseFormComponent, TESForm, TESFile, TESObjectCELL, BSString, NiPoint3: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Seek, GetFormType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); RVAs 0x1cd860, 0x1cd7d0.
// Callees and globals without a community name are bound to the RVA the image encodes; every
// such name is only a guess about what the callee does.
// GetOffsetData: GUESS(low); RVA 0x313020, the per-file offset record of a world space; a field at 0x18 is a file offset.
// OffsetData: GUESS(low); what GetOffsetData returns, only the file offset is read.
// IsRecordFileLoaded: GUESS(low); RVA 0x1ce3e0, a check on a plugin file before seeking in it.
// currentFormID: GUESS(low); TESFile member at 0x290, the id of the record the file is positioned at.
// CellAtCoordinates: GUESS(low); RVA 0x1b4b50, the cell of a world space at cell-grid coordinates.
// kRecordFormType: GUESS(low); global byte at RVA 0x20788b8, the record type a world space is stored under.
// kEmptyString: GUESS(low); global at RVA 0x1b58020, the empty text a BSString returns when it holds nothing.
// FloorToCell: GUESS(low); the cell-grid coordinate of a world position, 4096 units per cell.
// TESWorldSpace::IsParentForm, TESForm::IsParentForm: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); slot 34 of TESForm
#pragma once

#include <cstdint>

class TESObjectCELL;

// Empty text of a BSString (global in the image).
extern const char kEmptyString[];

// NiPoint3: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
struct NiPoint3 {
    float x;  // 00
    float y;  // 04
    float z;  // 08
};
static_assert(sizeof(NiPoint3) == 0xC, "layout");

struct OffsetData {
    std::uint8_t  unk00[0x18];  // 00
    std::uint32_t fileOffset;   // 18
};

// BSString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
struct BSString {
    const char* c_str() const
    {
        return data ? data : kEmptyString;
    }

    char*         data;      // 00
    std::uint16_t size;      // 08
    std::uint16_t capacity;  // 0A
    std::uint32_t pad0C;     // 0C
};
static_assert(sizeof(BSString) == 0x10, "layout");

// FormType: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); 32 bits wide, as the TESFile unit declares it
enum class FormType : std::uint32_t;

// TESFile: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class TESFile {
public:
    bool          Seek(std::uint32_t a_offset);
    FormType      GetFormType();
    bool          IsRecordFileLoaded();

    std::uint8_t  unk000[0x290];  // 000
    std::uint32_t currentFormID;  // 290
};

// BaseFormComponent: STANDIN EXE_RTTI; class name and base from the image RTTI, 4 primary vftable slots
// sizeof BaseFormComponent 0x8: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
class BaseFormComponent {
public:
    virtual ~BaseFormComponent();  // 00
    virtual void Unk_01();
    virtual void Unk_02();
    virtual void Unk_03();
};
static_assert(sizeof(BaseFormComponent) == 0x8, "layout");

// TESForm: STANDIN EXE_RTTI; class name and base from the image RTTI, 59 primary vftable slots
class TESForm : public BaseFormComponent {
public:
    ~TESForm() override;  // 00
    virtual void Unk_04();
    virtual void ClearData();  // 05
    virtual void Unk_06();
    virtual void Unk_07();
    virtual void Unk_08();
    virtual void Unk_09();
    virtual void Unk_0A();
    virtual void Unk_0B();
    virtual bool FindInFileFast(TESFile* a_mod);  // 0C
    virtual void Unk_0D();
    virtual void Unk_0E();
    virtual void Unk_0F();
    virtual void Unk_10();
    virtual void Unk_11();
    virtual void Unk_12();
    virtual void Unk_13();
    virtual void Unk_14();
    virtual void Unk_15();
    virtual void Unk_16();
    virtual void Unk_17();
    virtual void Unk_18();
    virtual void Unk_19();
    virtual void Unk_1A();
    virtual void Unk_1B();
    virtual void Unk_1C();
    virtual void Unk_1D();
    virtual void Unk_1E();
    virtual void Unk_1F();
    virtual void Unk_20();
    virtual void Unk_21();
    virtual void Unk_22();
    virtual void Unk_23();
    virtual void Unk_24();
    virtual void Unk_25();
    virtual void Unk_26();
    virtual void Unk_27();
    virtual void Unk_28();
    virtual void Unk_29();
    virtual void Unk_2A();
    virtual void Unk_2B();
    virtual void Unk_2C();
    virtual void Unk_2D();
    virtual void Unk_2E();
    virtual void Unk_2F();
    virtual void Unk_30();
    virtual void Unk_31();
    virtual const char* GetFormEditorID() const;  // 32
    virtual bool SetFormEditorID(const char* a_str);  // 33
    virtual bool IsParentForm();
    virtual void Unk_35();
    virtual bool IsFormTypeChild(std::uint8_t a_type);  // 36
    virtual void Unk_37();
    virtual void Unk_38();
    virtual void Unk_39();
    virtual void Unk_3A();

    void*         sourceFiles;       // 08
    std::uint32_t formFlags;         // 10
    std::uint32_t formID;            // 14
    std::uint16_t inGameFormFlags;   // 18
    std::uint8_t  formType;          // 1A
    std::uint8_t  pad1B[5];          // 1B
};
static_assert(sizeof(TESForm) == 0x20, "layout");

// FloorToCell: see the label above.
inline std::int32_t FloorToCell(float a_pos)
{
    float whole = static_cast<float>(static_cast<std::int32_t>(a_pos));
    return static_cast<std::int32_t>(a_pos - whole >= 0.0f ? whole : whole - 1.0f) >> 12;
}

// TESWorldSpace: EXE_RTTI; class name and base from the image RTTI, 59 primary vftable slots
// sizeof TESWorldSpace 0x358: OBSERVED; size argument of operator delete in the deleting destructor (slot 0)
// Other RTTI bases (not declared here; their vftable pointers lie inside the members): .?AVTESFullName@@, .?AVTESModel@@
class TESWorldSpace : public TESForm {
public:
    TESWorldSpace();
    ~TESWorldSpace() override;                           // 00
    void        ClearData() override;                    // 05
    bool        FindInFileFast(TESFile* a_mod) override;  // 0C
    const char* GetFormEditorID() const override;        // 32
    bool        SetFormEditorID(const char* a_str) override;  // 33
    bool        IsFormTypeChild(std::uint8_t a_type) override;  // 36
    bool        IsParentForm() override;            // 34

    TESObjectCELL* GetCellByPosition(const NiPoint3& a_pos) const;

    OffsetData*    GetOffsetData() const;
    TESObjectCELL* CellAtCoordinates(std::int32_t a_x, std::int32_t a_y) const;

    std::uint8_t unk20[0x1E0];  // 20
    BSString     editorID;      // 200
    std::uint8_t unk210[0x148];  // 210
};
static_assert(sizeof(TESWorldSpace) == 0x358, "layout");
