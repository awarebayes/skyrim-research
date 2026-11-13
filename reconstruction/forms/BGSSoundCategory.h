// BGSSoundCategory declarations for build sse-steam-1-7-104.
//
// Labels: v2
// Task: q2-s09-tesform-bgssoundcategory
// Source exposure: mixed (names and declarations from community headers; base classes, sizes and
// the compared functions from the pinned image).
// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and
// community names are unverified.
// Base form: shared header ../forms/TESForm.h for TESForm. The compared bodies reach fields by
// offset from this (attenuation at 0x1A lies inside TESForm, and the sound-category interface sits at
// 0x30 of a parent), so they use RawAt; header-gap TESForm for these fields.
// BGSSoundCategory: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT) EXE_RTTI
// BGSSoundCategory::SetCategoryAttenuation, BGSSoundCategory::SetCategoryFrequency, BGSSoundCategory::Matches: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// BGSSoundCategory::InitializeData: COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)
// BSISoundCategory: STANDIN COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
// BSISoundCategory::unk02, BSISoundCategory::unk03: GUESS(low)
// RawAt: GUESS(low)
#pragma once

#include <cstddef>
#include <cstdint>
#include "../forms/TESForm.h"

class BGSSoundCategory;

class BSISoundCategory
{
public:
    virtual ~BSISoundCategory();
    virtual bool Matches(const BSISoundCategory* a_category) const;  // slot 01
    virtual void unk02();  // slot 02
    virtual void unk03();  // slot 03
    virtual float GetCategoryFrequency() const;  // slot 04
};

template <class T>
T& RawAt(const void* a_base, std::ptrdiff_t a_offset)
{
    return *reinterpret_cast<T*>(const_cast<std::uint8_t*>(reinterpret_cast<const std::uint8_t*>(a_base)) + a_offset);
}

class BGSSoundCategory : public TESForm
{
public:
    virtual void SetCategoryAttenuation(std::uint16_t a_value);  // compared: 0x3299e0
    virtual void SetCategoryFrequency(float a_value);  // compared: 0x329970
    virtual void InitializeData();  // compared: 0x329790
    virtual bool Matches(const BSISoundCategory* a_category) const;  // compared: 0x329820
};
