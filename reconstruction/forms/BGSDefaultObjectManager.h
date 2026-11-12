// BGSDefaultObjectManager type declarations, build sse-steam-1-7-104.
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG
// b93280e832f263dbef44e44cbe2936622a02f91a (MIT) and meh321/AddressLibraryDatabase 0379cb6
// (used with the author's permission as reported by the maintainer). NG's size and member
// offsets are not used: this build has the object array at 0x20 and 0x174 entries.
// Adapted bodies: none declared in this header; tools/check_origin.py reports none above its
// threshold at the pinned community and sibling revisions.
// BaseFormComponent, TESForm and BGSEquipSlot are minimal stand-ins; the shared TESForm.h declares
// no TESForm constructor or out-of-line plain destructor, which this unit's code calls (header-gap TESForm).
// BaseFormComponent, TESForm, TESForm::InitializeData ... QAvailableInGame, TESForm::formFlags, ::formID, ::formType, ::sourceFiles: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the slot names 04 to 3A follow NG and only the slot order matters here
// TESForm::LookupByID, TESForm::kInitialized: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the address is the one the Address Library names TESDataHandler::GetForm (id 14617)
// BGSDefaultObjectManager, BGSDefaultObjectManager::InitItemImpl, ::Load, ::objects: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; NG declares objects with 0x1c3 entries, 0x174 here
// BGSDefaultObjectManager::GetLeftHandEquip, ::GetRightHandEquip, ::GetVoiceEquip, ::GetEquipSlot: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); static here, the listings take no this
// BGSDefaultObjectManager::GetDefaultObject: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission) OBSERVED; static, takes the object index and returns the form
// BGSDefaultObjectManager::objectInit: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; at 0xBC0 here
// DEFAULT_OBJECT_DATA, DEFAULT_OBJECT_DATA::type: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the table of 0x18-byte entries at the image's data segment
// DEFAULT_OBJECT_DATA::name, ::pad09, ::pad0A, ::uniqueID, ::doType, ::pad14: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BGSEquipSlot: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESForm::SetInitialized: GUESS(low); the call that marks the form initialised, at 0x1e60b0
// defaultObjectTable: GUESS(low); the table at RVA 0x207bf48 that NG calls the DEFAULT_OBJECT_DATA array
// BGSDefaultObjectManager::TestBit: GUESS(low); a flag-word bit test by bit index, taking the word by value (rule 16)
// LogProgressMarker: GUESS(low); the function at 0x31c530 called with a string at one object index
// DefaultObjectsInitializedEvent, GetDefaultObjectEventSource, SendDefaultObjectEvent: GUESS(low); the helpers at 0x31c080 and 0x31be40
// ResolveFormRedirect: GUESS(low); the function at 0x559a10 called with a form ID when the looked-up form has type 0xF
#pragma once

#include <cstdint>

enum class FormType : std::uint8_t {
    None = 0
};

using FormID = std::uint32_t;

class TESFile;
class BSFixedString;
class TESObjectREFR;
class TESBoundObject;
class FORM;
class FORM_GROUP;
class BGSSaveFormBuffer;
class BGSLoadFormBuffer;

class BaseFormComponent {
public:
    virtual ~BaseFormComponent();                            // 00
    virtual void InitializeDataComponent() = 0;              // 01
    virtual void ClearDataComponent() = 0;                   // 02
    virtual void CopyComponent(BaseFormComponent* a_rhs);    // 03
};

class TESForm : public BaseFormComponent {
public:
    TESForm();
    ~TESForm() override;                                    // 00
    void InitializeDataComponent() override;                // 01
    void ClearDataComponent() override;                     // 02
    void CopyComponent(BaseFormComponent* a_rhs) override;  // 03

    virtual void                       InitializeData();                                       // 04
    virtual void                       ClearData();                                            // 05
    virtual bool                       Load(TESFile* a_mod);                                   // 06
    virtual bool                       LoadPartial(TESFile* a_mod);                            // 07
    virtual bool                       LoadEdit(TESFile* a_mod);                               // 08
    virtual TESForm*                   CreateDuplicateForm(bool a_createEditorID, void* a_arg2);  // 09
    virtual bool                       AddChange(std::uint32_t a_changeFlags);                 // 0A
    virtual void                       RemoveChange(std::uint32_t a_changeFlags);              // 0B
    virtual bool                       FindInFileFast(TESFile* a_mod);                         // 0C
    virtual bool                       CheckSaveGame(BGSSaveFormBuffer* a_buf);                // 0D
    virtual void                       SaveGame(BGSSaveFormBuffer* a_buf);                     // 0E
    virtual void                       LoadGame(BGSLoadFormBuffer* a_buf);                     // 0F
    virtual void                       InitLoadGame(BGSLoadFormBuffer* a_buf);                 // 10
    virtual void                       FinishLoadGame(BGSLoadFormBuffer* a_buf);               // 11
    virtual void                       Revert(BGSLoadFormBuffer* a_buf);                       // 12
    virtual void                       InitItemImpl();                                         // 13
    virtual TESFile*                   GetDescriptionOwnerFile() const;                        // 14
    virtual FormType                   GetSavedFormType() const;                               // 15
    virtual void                       GetFormDetailedString(char* a_buf, std::uint32_t a_bufLen);  // 16
    virtual bool                       GetKnown() const;                                       // 17
    virtual bool                       GetRandomAnim() const;                                  // 18
    virtual bool                       GetPlayable() const;                                    // 19
    virtual bool                       IsHeadingMarker() const;                                // 1A
    virtual bool                       GetDangerous() const;                                   // 1B
    virtual bool                       QHasCurrents() const;                                   // 1C
    virtual bool                       GetObstacle() const;                                    // 1D
    virtual bool                       QIsLODLandObject() const;                               // 1E
    virtual bool                       GetOnLocalMap() const;                                  // 1F
    virtual bool                       GetMustUpdate() const;                                  // 20
    virtual void                       SetOnLocalMap(bool a_set);                              // 21
    virtual bool                       GetIgnoredBySandbox() const;                            // 22
    virtual void                       SetDelete(bool a_set);                                  // 23
    virtual void                       SetAltered(bool a_set);                                 // 24
    virtual void                       SaveObjectBound();                                      // 25
    virtual void                       LoadObjectBound(TESFile* a_mod);                        // 26
    virtual bool                       IsBoundObject() const;                                  // 27
    virtual bool                       IsObject() const;                                       // 28
    virtual bool                       IsMagicItem() const;                                    // 29
    virtual bool                       IsWater() const;                                        // 2A
    virtual TESObjectREFR*             AsReference1();                                         // 2B
    virtual const TESObjectREFR*       AsReference2() const;                                   // 2C
    virtual std::uint32_t              GetRefCount() const;                                    // 2D
    virtual const char*                GetTextForParsedSubTag(const BSFixedString& a_tag) const;  // 2E
    virtual void                       Copy(TESForm* a_srcForm);                               // 2F
    virtual bool                       BelongsInGroup(FORM* a_form, bool a_allowParentGroups, bool a_currentOnly);  // 30
    virtual void                       CreateGroupData(FORM* a_form, FORM_GROUP* a_group);     // 31
    virtual const char*                GetFormEditorID() const;                                // 32
    virtual bool                       SetFormEditorID(const char* a_str);                     // 33
    virtual bool                       IsParentForm();                                         // 34
    virtual bool                       IsParentFormTree();                                     // 35
    virtual bool                       IsFormTypeChild(FormType a_type);                       // 36
    virtual bool                       Activate(TESObjectREFR* a_targetRef, TESObjectREFR* a_activatorRef, std::uint8_t a_arg3, TESBoundObject* a_object, std::int32_t a_targetCount);  // 37
    virtual void                       SetFormID(FormID a_id, bool a_updateFile);              // 38
    virtual const char*                GetObjectTypeName() const;                              // 39
    virtual bool                       QAvailableInGame() const;                               // 3A

    static TESForm* LookupByID(FormID a_formID);
    void            SetInitialized(bool a_set);

    // members
    void*         sourceFiles;       // 08
    std::uint32_t formFlags;         // 10
    FormID        formID;            // 14
    std::uint16_t inGameFormFlags;   // 18
    FormType      formType;          // 1A
    std::uint8_t  pad1B;             // 1B
    std::uint32_t pad1C;             // 1C
};
static_assert(sizeof(TESForm) == 0x20, "layout");

class BGSEquipSlot : public TESForm {
};

struct DEFAULT_OBJECT_DATA {
    const char*   name;         // 00
    FormType      type;         // 08
    std::uint8_t  pad09;        // 09
    std::uint16_t pad0A;        // 0A
    char          uniqueID[4];  // 0C
    std::uint32_t doType;       // 10
    std::uint32_t pad14;        // 14
};
static_assert(sizeof(DEFAULT_OBJECT_DATA) == 0x18, "layout");

class BGSDefaultObjectManager : public TESForm {
public:
    static constexpr std::uint32_t kTotal = 0x174;

    BGSDefaultObjectManager();
    ~BGSDefaultObjectManager() override;  // 00
    bool Load(TESFile* a_mod) override;   // 06
    void InitItemImpl() override;         // 13

    static TESForm*      GetDefaultObject(std::uint32_t a_index);
    static BGSEquipSlot* GetLeftHandEquip();
    static BGSEquipSlot* GetRightHandEquip();
    static BGSEquipSlot* GetVoiceEquip();
    static BGSEquipSlot* GetEquipSlot(std::uint32_t a_which);

    // members
    TESForm*     objects[kTotal];     // 20
    bool         objectInit[kTotal];  // BC0
    std::uint8_t pad_end[4];          // D34

};
static_assert(sizeof(BGSDefaultObjectManager) == 0xD38, "size");
