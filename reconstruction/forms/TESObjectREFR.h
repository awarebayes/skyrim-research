// Type declarations for the TESObjectREFR unit (build sse-steam-1-7-104).
//
// Labels: v2
// Source exposure: mixed (binary-analysis of the pinned image, community-headers).
// Names follow CharmedBaryon/CommonLibSSE-NG b93280e832f263dbef44e44cbe2936622a02f91a (MIT)
// and powerof3/CommonLibSSE 654e55f7979c1733033d5dbef176e43827bac944 (GPL-3.0); no community
// code is copied. Every class other than TESObjectREFR is a minimal stand-in that declares only
// the members and virtual slots the compared code needs, so the layouts of the stand-ins are not
// claimed to match the game. Unk_NN placeholders only keep the compared virtual slots at the
// vtable offsets the image encodes (slot NN is the byte offset NN * 8).
// TESObjectREFR, GetScale, GetCurrentLocation, GetCalcLevel, GetTransform: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// Callees without a community name are bound to the RVA the image encodes, and every such name
// is only a guess about what the callee does.
#pragma once

#include <cstdint>

class BGSLocation;
class TESObjectREFR;

// FormType FormType::NPC FormType::ActorCharacter: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); only the values used here.
enum class FormType : std::uint8_t {
    NPC            = 0x2B,
    ActorCharacter = 0x3E,
};

// NiPoint3, NiMatrix3, NiTransform: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
struct NiPoint3 {
    float x;  // 00
    float y;  // 04
    float z;  // 08
};

struct NiMatrix3 {
    float entry[3][3];  // 00

    // SetEulerAngles: GUESS(low); the callee at RVA 0xede280 takes the matrix and three floats.
    void SetEulerAngles(float a_x, float a_y, float a_z);
};

struct NiTransform {
    NiMatrix3 rotate;     // 00
    NiPoint3  translate;  // 24
    float     scale;      // 30
};

// TESForm: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class TESForm {
public:
    virtual ~TESForm();  // 00
    virtual void Unk_01();
    virtual void Unk_02();
    virtual void Unk_03();
    virtual void Unk_04();
    virtual void Unk_05();
    virtual void Unk_06();
    virtual void Unk_07();
    virtual void Unk_08();
    virtual void Unk_09();
    virtual void Unk_0A();
    virtual void Unk_0B();
    virtual void Unk_0C();
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
    virtual void Unk_32();
    virtual void Unk_33();
    virtual void Unk_34();
    virtual void Unk_35();
    virtual void Unk_36();
    virtual void Unk_37();
    virtual void Unk_38();
    virtual void Unk_39();
    virtual void Unk_3A();

    void*         sourceFiles;       // 08
    std::uint32_t formFlags;         // 10
    std::uint32_t formID;            // 14
    std::uint16_t inGameFormFlags;   // 18
    FormType      formType;          // 1A
    std::uint8_t  pad1B[5];          // 1B
};

// TESBoundObject: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the object a
// reference points at.
class TESBoundObject : public TESForm {
};

// TESNPC: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class TESNPC : public TESBoundObject {
public:
    // GetHeightScale: GUESS(low); the callee at RVA 0x3c65c0 returns a float that scales an NPC
    // reference.
    float GetHeightScale() const;
};

// TESWorldSpace: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class TESWorldSpace {
public:
    // LookupLocation: GUESS(low); the callee at RVA 0x310ff0 maps a position to a location.
    BGSLocation* LookupLocation(const NiPoint3& a_pos) const;
};

// TESObjectCELL: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class TESObjectCELL : public TESForm {
public:
    BGSLocation* GetLocation() const;  // RVA 0x2bb180

    std::uint8_t   unk20[0x20];
    std::uint8_t   cellFlags;      // 40
    std::uint8_t   unk41[0xE7];
    TESWorldSpace* worldSpace;     // 128
};

// ExtraDataList: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class ExtraDataList {
public:
    // GetExtraLocation: GUESS(low); the callee at RVA 0x16a1f0 reads a location from the list.
    BGSLocation* GetExtraLocation() const;

    std::uint8_t unk00[0x28];
};

// BGSEncounterZone: STANDIN COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0)
class BGSEncounterZone {
public:
    std::uint8_t  unk00[0x44];
    std::uint16_t unk44;  // 44

    // GetLevelFromData: GUESS(low); the callee at RVA 0x28f9e0 yields a level for the zone.
    std::uint16_t GetLevelFromData() const;
};

// BSHandleRefObject, IAnimationGraphManagerHolder: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); bases of TESObjectREFR, only their sizes matter here.
// BSAnimationGraphEventSink: STANDIN GUESS; stands in for NG's BSTEventSink<BSAnimationGraphEvent> base at 0x30, only its size matters.
class BSHandleRefObject {
public:
    virtual ~BSHandleRefObject();
    std::uint32_t refCount;  // 08
    std::uint32_t pad0C;     // 0C
};

class BSAnimationGraphEventSink {
public:
    virtual ~BSAnimationGraphEventSink();
};

class IAnimationGraphManagerHolder {
public:
    virtual ~IAnimationGraphManagerHolder();
};

// OBJ_REFR: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
struct OBJ_REFR {
    TESBoundObject* objectReference;  // 00
    NiPoint3        angle;            // 08
    NiPoint3        location;         // 14
};

// PlayerCharacter: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
class PlayerCharacter {
public:
    // singleton: GUESS; global pointer at RVA 0x3230778, which NG reads through PlayerCharacter::GetSingleton (RE::Offset::PlayerCharacter::Singleton).
    static PlayerCharacter* singleton;

    // GetLevel: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); Actor::GetLevel, RVA 0x6797a0.
    std::uint16_t GetLevel();

    std::uint8_t  unk00[0xAD8];
    // currentLocation: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) GUESS(medium); NG names a PlayerCharacter member currentLocation at SE offset 0xac8; that 0xad8 here is the same member is the guess.
    BGSLocation*  currentLocation;  // AD8
};

// TESObjectREFR: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); members at the offsets
// the compared functions read.
class TESObjectREFR :
    public TESForm,                      // 00
    public BSHandleRefObject,            // 20
    public BSAnimationGraphEventSink,    // 30
    public IAnimationGraphManagerHolder  // 38
{
public:
    virtual void Unk_3B();
    virtual void Unk_3C();
    virtual void Unk_3D();
    virtual void Unk_3E();
    virtual void Unk_3F();
    virtual void Unk_40();
    virtual void Unk_41();
    virtual void Unk_42();
    virtual void Unk_43();
    virtual void Unk_44();
    virtual void Unk_45();
    virtual void Unk_46();
    virtual void Unk_47();
    virtual void Unk_48();
    virtual void Unk_49();
    virtual void Unk_4A();
    virtual void Unk_4B();
    virtual void Unk_4C();
    virtual void Unk_4D();
    virtual void Unk_4E();
    virtual void Unk_4F();
    virtual void Unk_50();
    virtual void Unk_51();
    virtual void Unk_52();
    virtual void Unk_53();
    virtual void Unk_54();
    virtual void Unk_55();
    virtual void Unk_56();
    virtual void Unk_57();
    virtual void Unk_58();
    virtual void Unk_59();
    virtual void Unk_5A();
    virtual void Unk_5B();
    virtual void Unk_5C();
    virtual void Unk_5D();
    virtual void Unk_5E();
    virtual void Unk_5F();
    virtual void Unk_60();
    virtual void Unk_61();
    virtual void Unk_62();
    virtual void Unk_63();
    virtual void Unk_64();
    virtual void Unk_65();
    virtual void Unk_66();
    virtual void Unk_67();
    virtual void Unk_68();
    virtual void Unk_69();
    virtual void Unk_6A();
    virtual void Unk_6B();
    virtual void Unk_6C();
    virtual void Unk_6D();
    virtual void Unk_6E();
    virtual void Unk_6F();
    virtual void Unk_70();
    virtual void Unk_71();
    virtual void Unk_72();
    virtual void Unk_73();
    virtual void Unk_74();
    virtual void Unk_75();
    virtual void Unk_76();
    virtual void Unk_77();
    virtual void Unk_78();
    virtual void Unk_79();
    virtual void Unk_7A();
    virtual void Unk_7B();
    virtual void Unk_7C();
    virtual void Unk_7D();
    virtual void Unk_7E();
    virtual void Unk_7F();
    virtual void Unk_80();
    virtual void Unk_81();
    virtual void Unk_82();
    virtual void Unk_83();
    virtual void Unk_84();
    virtual void Unk_85();
    virtual void Unk_86();
    virtual void Unk_87();
    virtual void Unk_88();
    virtual void Unk_89();
    virtual void Unk_8A();
    virtual void Unk_8B();
    virtual void Unk_8C();
    virtual void Unk_8D();
    virtual void Unk_8E();
    virtual void Unk_8F();
    virtual void Unk_90();
    virtual void Unk_91();
    virtual void Unk_92();
    virtual void Unk_93();
    virtual void Unk_94();
    virtual void Unk_95();
    virtual void Unk_96();
    // GetSaveParentCell: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); virtual slot 0x97.
    virtual TESObjectCELL* GetSaveParentCell() const;  // 97

    float         GetScale() const;
    BGSLocation*  GetCurrentLocation() const;
    std::uint16_t GetCalcLevel(bool a_adjustLevel) const;
    void          GetTransform(NiTransform& a_transform) const;

    // GetEncounterZone: COMMUNITY(powerof3/CommonLibSSE@654e55f, GPL-3.0); RVA 0x300ab0.
    BGSEncounterZone* GetEncounterZone() const;

    OBJ_REFR       data;         // 40
    TESObjectCELL* parentCell;   // 60
    void*          loadedData;   // 68
    ExtraDataList  extraList;    // 70
    std::uint16_t  refScale;     // 98

    // As: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the checked downcast on references.
    template <class T>
    const T* As() const;
};

// Actor: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT); the character reference type that GetTransform tests for.
class Actor : public TESObjectREFR {
public:
    static constexpr FormType FORMTYPE = FormType::ActorCharacter;
};

template <class T>
const T* TESObjectREFR::As() const
{
    return formType == T::FORMTYPE ? static_cast<const T*>(this) : nullptr;
}
