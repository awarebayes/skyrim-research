// Origin: original reconstruction
// BGSMaterialType declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p92-n-bgsmaterialtype
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm.
// BGSMaterialType: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSMaterialType::ClearData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
#pragma once

#include <cstdint>
#include <cstddef>
#include "../forms/TESForm.h"

// BSFixedString, BSFixedString::~BSFixedString: STANDIN COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// value, parent, materialName, materialKind, color, buoyancy, flags, impact,
// MaterialColor, red, green, blue, defaultMaterialColor: GUESS(low); represented material fields and defaults.
class BSFixedString { public: BSFixedString(const char*); ~BSFixedString(); BSFixedString& operator=(const BSFixedString&); const char* value; };
struct MaterialColor { float red, green, blue; };
extern MaterialColor defaultMaterialColor;
class BGSMaterialType : public TESForm {
public:
    void ClearData() override;
    BGSMaterialType* parent;
    BSFixedString materialName;
    std::uint32_t materialKind;
    MaterialColor color;
    float buoyancy;
    std::uint32_t flags;
    void* impact;
};
static_assert(sizeof(BGSMaterialType)==0x50, "material type size");
