// BSProceduralLightningController functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-bsprocedurallightningcontroller
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).
// Evidence: findings/queue-normal-selection.md
// Recipe: reconstruction/recipes/msvc-19.16.27054-o2.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5, worker haiku-202611122349-3), starting from
// a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xffd880, 12 bytes: BSProceduralLightningController::GetInterpolator
//   RVA 0xffd7d0, 24 bytes: BSProceduralLightningController::GetInterpolatorID
//   RVA 0xffc810, 99 bytes: BSProceduralLightningController::LoadBinary
//   RVA 0xffe540, 113 bytes: BSProceduralLightningController::InterpolatorIsCorrectType
//   RVA 0xffc920, 142 bytes: BSProceduralLightningController::RegisterStreamables
//   RVA 0xffca50, 345 bytes: BSProceduralLightningController::IsEqual (set aside in near-miss/0xffca50.cpp)
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "BSProceduralLightningController.h"

// RVA 0xffd880, 12 bytes.
NiInterpolator* BSProceduralLightningController::GetInterpolator(std::uint16_t a_index) const
{
    return interpolators[a_index];
}

// RVA 0xffd7d0, 24 bytes.
const char* BSProceduralLightningController::GetInterpolatorID(std::uint16_t a_index)
{
    if (a_index < 9) {
        return g_procLightningIDNames[a_index];
    }
    return nullptr;
}

// RVA 0xffc810, 99 bytes.
void BSProceduralLightningController::LoadBinary(NiStream& a_stream)
{
    NiTimeController_LoadBinary(this, a_stream);
    for (std::size_t i = 9; i != 0; --i) {
        StreamReadSlot(a_stream);
    }
    ReadStreamSubA(subA, a_stream);
    ReadStreamSubB(subB, a_stream);
    StreamReadSlot(a_stream);
}

// RVA 0xffe540, 113 bytes.
bool BSProceduralLightningController::InterpolatorIsCorrectType(NiInterpolator* a_interpolator, std::uint16_t a_index) const
{
    if (a_index > 1) {
        if (a_index > 8 || a_interpolator == nullptr) {
            return false;
        }
        for (const NiRTTI* rtti = a_interpolator->GetRTTI(); rtti != nullptr; rtti = rtti->parent) {
            if (rtti == &NiRTTI_NiFloatInterpolator) {
                return true;
            }
        }
        return false;
    }
    if (a_interpolator == nullptr) {
        return false;
    }
    return a_interpolator->GetRTTI() == &NiRTTI_NiBoolTimelineInterpolator;
}

// RVA 0xffc920, 142 bytes.
bool BSProceduralLightningController::RegisterStreamables(NiStream& a_stream)
{
    bool result = NiTimeController_RegisterStreamables(this, a_stream);
    if (result) {
        NiInterpolator** slot = interpolators;
        for (std::size_t i = 9; i != 0; --i) {
            if (*slot) {
                (*slot)->RegisterStreamables(a_stream);
            }
            ++slot;
        }
        if (object100) {
            object100->RegisterStreamables(a_stream);
        }
    }
    return result;
}

// Retained generated leaf; its byte-match evidence is renewed with this unit.
// GetInterpolatorCount: COMMUNITY(meh321/AddressLibraryDatabase@0379cb6, permission)
std::uint32_t BSProceduralLightningController::GetInterpolatorCount() const
{
    return 0x9;
}
