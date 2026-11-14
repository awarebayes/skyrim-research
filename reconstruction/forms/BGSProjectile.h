// Build: sse-steam-1-7-104
// Labels: v2
// Source exposure: mixed (community headers and pinned-image analysis).
// Code origin: original reconstruction; declarations adapted from the pinned MIT community headers.
// Drafted by gpt-6.1-sol, Engineers p105 and p115. Adapted bodies: none.
// Declarations adapt CharmedBaryon/CommonLibSSE-NG@b93280e832f263dbef44e44cbe2936622a02f91a (MIT).
// Helper spellings and local variable names are inferred; individual labels accompany declarations.
// MIT License
// 
// Copyright (c) 2018 Ryan-rsm-McKenzie
// 
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
// 
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
// 
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.
// BGSProjectile: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
#pragma once
#include <cstdint>
#include <cstddef>
// Localized TESForm declarations; their MIT notice is retained above.
// Type declarations for the TESForm unit (build sse-steam-1-7-104).
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names and member offsets follow CharmedBaryon/CommonLibSSE-NG
// b93280e832f263dbef44e44cbe2936622a02f91a (MIT) and meh321/AddressLibraryDatabase 0379cb6
// (used with the author's permission as reported by the maintainer).
// Adapted bodies: none declared; tools/check_origin.py reports none above its threshold (0.75)
// at CommonLibSSE-NG b93280e, powerof3/CommonLibSSE 654e55f and momusdigital/fnv_decomp 91e1b6e8.
// TESForm::ClearData's empty body necessarily coincides with the FNV decompilation's.
// Every class other than TESForm and
// BaseFormComponent is a minimal stand-in that declares only the members and virtual slots the
// compared code needs; the layouts of the stand-ins are not claimed to match the game.
// BaseFormComponent, TESForm, TESForm::ClearData, ::SaveGame, ::LoadGame, ::CopyComponent, ::GetGoldValue: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESForm::InitializeData, ::AsReference2, ::SetAltered: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the other slot names 04 to 3A follow the NG header too and only the slot order matters here
// TESForm::sourceFiles, ::formFlags, ::formID, ::inGameFormFlags, ::formType, ::pad1B, ::pad1C: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESForm::RecordFlags, ::ChangeFlags, kAltered, kPersistent, kTemporary, kFlags: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESForm::InGameFormFlag: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESForm::IsPersistent, ::IsTemporaryFormID, ::GetEnchantment: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); NG declares IsPersistent only on TESObjectREFR
// TESForm::GetGoldValue: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission); id 14978 names this address; NG declares the name but implements it itself
// TESFileContainer, TESFileArray: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the array layout (data, size) is read from the listings
// TESFile: STANDIN COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// TESDataHandler, TESDataHandler::IsTemporaryFormID: STANDIN COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// TESDataHandler::singleton: GUESS(low); the global pointer at RVA 0x219ded8, which NG reads through GetSingleton
// ExtraDataList, ExtraDataList::GetEnchantment: STANDIN COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// EnchantmentItem, TESEnchantableForm, TESEnchantableForm::formEnchanting, TESValueForm, TESValueForm::value, MagicItem, MagicItem::CalculateCost, AlchemyItem: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// TESEnchantableForm, TESValueForm, MagicItem, AlchemyItem: EXE_RTTI; the names of the type descriptors the casts use, read from the image RTTI
// BGSSaveGameBuffer, BGSSaveFormBuffer, BGSSaveGameBuffer::SaveDataEndian, BGSSaveFormBuffer::unk18: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) OBSERVED; SaveDataEndian takes more parameters than NG declares
// BGSSaveFormBuffer::unk1B: GUESS(low); a byte at offset 0x1B whose bit 0 SaveGame tests; NG declares the region only as unk18
// BGSLoadGameBuffer, BGSLoadFormBuffer, BGSLoadGameBuffer::LoadDataEndian, BGSLoadFormData::changeFlags: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>

enum class FormType : std::uint8_t {
    None = 0
};

using FormID = std::uint32_t;

class BSFixedString;
class TESObjectREFR;
class TESBoundObject;
class FORM;
class FORM_GROUP;
class BGSSaveFormBuffer;
class BGSLoadFormBuffer;
class EnchantmentItem;

class BaseFormComponent {
public:
    virtual ~BaseFormComponent();                            // 00
    virtual void InitializeDataComponent() = 0;              // 01
    virtual void ClearDataComponent() = 0;                   // 02
    virtual void CopyComponent(BaseFormComponent* a_rhs);    // 03
};


class Actor;
class TESFile;

struct TESFileArray {
    TESFile**     data;  // 00
    std::uint32_t size;  // 08
};

class TESFileContainer {
public:
    TESFileArray* array;  // 0
};

class ExtraDataList {
public:
    EnchantmentItem* GetEnchantment();
};

class TESForm : public BaseFormComponent {
public:
    struct ChangeFlags {
        enum ChangeFlag : std::uint32_t {
            kCreated = 0,
            kFlags   = 1 << 0
        };
    };

    struct RecordFlags {
        enum RecordFlag : std::uint32_t {
            kAltered    = 1 << 1,
            kPersistent = 1 << 10,
            kTemporary  = 1 << 14
        };
    };

    enum class InGameFormFlag : std::uint16_t {
        kNone = 0
    };

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

    std::int32_t     GetGoldValue() const;
    EnchantmentItem* GetEnchantment(ExtraDataList* a_extraList);
    bool             IsPersistent() const;
    bool             IsTemporaryFormID() const;

    // members
    TESFileContainer sourceFiles;      // 08
    std::uint32_t    formFlags;        // 10
    FormID           formID;           // 14
    std::uint16_t    inGameFormFlags;  // 18
    FormType         formType;         // 1A
    std::uint8_t     pad1B;            // 1B
    std::uint32_t    pad1C;            // 1C
};
static_assert(sizeof(TESForm) == 0x20, "layout");

class TESEnchantableForm : public BaseFormComponent {
public:
    EnchantmentItem* formEnchanting;  // 08
    std::uint32_t    unk10;           // 10
    std::uint32_t    pad14;           // 14
};

class TESValueForm : public BaseFormComponent {
public:
    std::int32_t  value;   // 08
    std::uint32_t pad0C;   // 0C
};

class MagicItem : public TESForm {
public:
    float CalculateCost(Actor* a_caster) const;
};

class AlchemyItem : public MagicItem {
};

class BGSSaveGameBuffer {
public:
    virtual ~BGSSaveGameBuffer();  // 00

    void SaveDataEndian(const void* a_data, std::uint32_t a_size, std::uint32_t a_count, std::uint32_t a_arg4);

    void*         buffer;          // 08
    std::uint32_t size;            // 10
    std::uint32_t bufferPosition;  // 14
};

class BGSSaveFormBuffer : public BGSSaveGameBuffer {
public:
    std::uint8_t  unk18[3];  // 18
    std::uint8_t  unk1B;     // 1B, bit 0 tested by SaveGame (seen in the listing)
    std::uint32_t unk1C;     // 1C
    std::uint64_t unk20;  // 20
    TESForm*      form;   // 28
};

class BGSLoadGameBuffer {
public:
    virtual ~BGSLoadGameBuffer();  // 00

    void LoadDataEndian(void* a_data, std::uint32_t a_offset, std::uint32_t a_size);

    void*         buffer;          // 08
    std::uint64_t unk10;           // 10
    std::uint32_t unk18;           // 18
    std::uint32_t unk1C;           // 1C
    std::uint32_t unk20;           // 20
    std::uint32_t bufferPosition;  // 24
};

class BGSLoadFormBuffer : public BGSLoadGameBuffer {
public:
    FormID        formID;            // 28
    std::uint32_t size;              // 2C
    std::uint32_t uncompressedSize;  // 30
    std::uint32_t pad34;             // 34
    TESForm*      form;              // 38
    std::uint32_t changeFlags;       // 40
    std::uint32_t oldChangeFlags;    // 44
};

class TESDataHandler {
public:
    bool IsTemporaryFormID(FormID a_formID);

    static TESDataHandler* singleton;
};

// The following bases and members represent the AE object rather than allocation-size storage.
// NiRefObject, BSHandleRefObject, BSTEventSink, IAnimationGraphManagerHolder, NiPoint3, NiTransform, OBJ_REFR, BaseExtraList, ReferenceExtraDataList, TESObjectREFR, Projectile: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class NiRefObject { public: virtual ~NiRefObject(); virtual void DeleteThis(); volatile std::uint32_t refCount; };
class BSHandleRefObject : public NiRefObject { public: ~BSHandleRefObject() override; };
class BSAnimationGraphEvent;
template<class T> class BSTEventSink { public: virtual ~BSTEventSink(); virtual void ProcessEvent(); };
class IAnimationGraphManagerHolder { public: virtual ~IAnimationGraphManagerHolder(); virtual void Unk01(); };
struct NiPoint3 { float x,y,z; };
struct NiTransform { float rotate[3][3]; NiPoint3 translate; float scale; };
struct OBJ_REFR { TESBoundObject* objectReference; NiPoint3 angle,location; };
class BSExtraData;
class BaseExtraList { public: virtual ~BaseExtraList(); BSExtraData* data; void* presence; };
struct ReferenceExtraDataList { BaseExtraList data; std::uint32_t threadID,lock; };
class TESObjectREFR : public TESForm, public BSHandleRefObject, public BSTEventSink<BSAnimationGraphEvent>, public IAnimationGraphManagerHolder {
public:
 virtual ~TESObjectREFR();
 OBJ_REFR data; void* parentCell; void* loadedData; ReferenceExtraDataList extraList;
 std::uint64_t unk90; std::uint16_t refScale; std::int8_t modelState; bool preDestroyed;
};
static_assert(sizeof(TESObjectREFR)==0xA0,"AE reference size");
struct ProjectileImpactList { void* item; void* next; };
struct ProjectileSoundHandle { std::uint32_t soundID; bool assumeSuccess; std::uint8_t state; std::uint16_t unknown6; std::uint32_t unknown8; };
class Projectile : public TESObjectREFR {
public:
 Projectile();
 void LoadGame(BGSLoadFormBuffer*); void SaveGame(BGSSaveFormBuffer*);
 ProjectileImpactList impacts;
 NiTransform transform; float unkE4; void* shapePhantom; std::uint32_t lockThread,lockCount;
 NiPoint3 velocity,linearVelocity;
 void* light; void* unk118; void* actorCause;
 std::uint32_t shooter,desiredTarget;
 ProjectileSoundHandle sound,countdown;
 std::uint32_t* unk148; void* inventoryEntry; void* explosion; void* spell;
 std::uint32_t castingSource; void* avEffect; void* queuedFiles;
 std::uint64_t unk180,unk188;
 float power,speedMult,range,livingTime,weaponDamage,transparency,explosionTimer;
 std::uint32_t unk1AC; float unk1B0,unk1B4; void* weaponSource; void* ammoSource;
 float distanceMoved; std::uint32_t unk1CC; float scale; std::uint32_t flags;
 bool unk1D8,unk1D9;
};
static_assert(sizeof(Projectile)==0x1E0,"AE projectile size");

inline BaseFormComponent::~BaseFormComponent() {}
class BSFixedString { public: BSFixedString(); ~BSFixedString(); const char* value; };
class TESFullName : public BaseFormComponent { public: ~TESFullName() override {} void InitializeDataComponent() override; void ClearDataComponent() override; void CopyComponent(BaseFormComponent*) override; virtual std::uint32_t GetFullNameLength() const; virtual const char* GetFullName() const; BSFixedString fullName; };
class TESModel : public BaseFormComponent { public: ~TESModel() override; void InitializeDataComponent() override; void ClearDataComponent() override; void CopyComponent(BaseFormComponent*) override; virtual const char* GetModel() const; virtual void SetModel(const char*); virtual void* GetAsModelTextureSwap(); BSFixedString model; void* textures; std::uint32_t* addons; std::uint16_t numTextures,numAddons; };
class TESObject : public TESForm {};
class TESBoundObject : public TESObject { public: virtual ~TESBoundObject(); std::int16_t boundMin[3],boundMax[3]; };
class BGSPreloadable : public BaseFormComponent { public: ~BGSPreloadable() override {} void InitializeDataComponent() override; void ClearDataComponent() override; void CopyComponent(BaseFormComponent*) override; virtual void Preload(); };
class TESImageSpaceModifiableForm : public BaseFormComponent { public: ~TESImageSpaceModifiableForm() override {} void InitializeDataComponent() override; void ClearDataComponent() override; void CopyComponent(BaseFormComponent*) override; void* imageSpaceModifier; };
class BGSDestructibleObjectForm : public BaseFormComponent { public: ~BGSDestructibleObjectForm() override; void InitializeDataComponent() override; void ClearDataComponent() override; void CopyComponent(BaseFormComponent*) override; void* destructibleData; };
struct BGSProjectileData { union { struct { union { struct { std::uint16_t flags,types; }; std::uint32_t flagsAndType; }; float gravity; }; std::uint64_t initialWord; }; float speed,range; void* light; void* muzzleFlashLight; float tracerChance,explosionProximity,explosionTimer; void* explosionType; void* activeSoundLoop; float muzzleFlashDuration,fadeOutTime,force; void* countdownSound; void* deactivateSound; void* defaultWeaponSource; float coneSpread,collisionRadius,lifetime,relaunchInterval; void* decalData; void* collisionLayer; };
class BSString;
class BGSProjectile : public TESBoundObject, public TESFullName, public TESModel, public BGSPreloadable, public BGSDestructibleObjectForm { public: void InitializeData() override; virtual void UnClone3D(TESObjectREFR*); virtual bool GetActivateText(TESObjectREFR*,BSString&); BGSProjectileData projectileData; TESModel muzzleFlashModel; std::uint32_t soundLevel; }; static_assert(sizeof(BGSProjectile)==0x138,"projectile form size");
void UnCloneProjectile(BGSProjectile*,TESObjectREFR*); void RemoveProjectileClone(BGSProjectile*,TESObjectREFR*); std::int16_t ProjectileCount(void*); bool ProjectileCrime(TESObjectREFR*); const char* ProjectileName(TESObjectREFR*); void FormatProjectileText(BSString*,const char*,...); extern const char* TakeProjectileText; extern const char* StealProjectileText; extern float DefaultProjectileRelaunch;

