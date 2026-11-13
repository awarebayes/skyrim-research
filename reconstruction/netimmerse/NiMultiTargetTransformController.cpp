// NiMultiTargetTransformController functions for build sse-steam-1-7-104.
//
// Labels: v2
// Task: p46-n-nimultitargettransformcontroller
// Source exposure: mixed (names and declarations from community headers; the listing of the pinned
// image).
// Evidence: findings/queue-normal-selection.md
// Recipe: reconstruction/recipes/o2-fpfast.json (compile this file alone).
// Drafted by Claude Haiku 5.5 (claude-haiku-5-5), starting from a tools/skeleton.py skeleton.
// Compared functions:
//   RVA 0xf5de10, 5 bytes: NiMultiTargetTransformController::GetInterpolatorCount
//   RVA 0xf5de20, 16 bytes: NiMultiTargetTransformController::GetInterpolatorID
//   RVA 0xf5b520, 52 bytes: NiMultiTargetTransformController::~NiMultiTargetTransformController
//   RVA 0xf5e280, 108 bytes: NiMultiTargetTransformController::GuaranteeTimeRange
//   RVA 0xf5de40, 120 bytes: NiMultiTargetTransformController::GetInterpolatorIndex
//   RVA 0xf5d7a0, 147 bytes: NiMultiTargetTransformController::LoadBinary
//   RVA 0xf5d860, 147 bytes: NiMultiTargetTransformController::SaveBinary
//   RVA 0xf5d900, 151 bytes: NiMultiTargetTransformController::IsEqual
//   RVA 0xf5df30, 203 bytes: NiMultiTargetTransformController::ResetTimeExtrema
//   RVA 0xf5e350, 308 bytes: NiMultiTargetTransformController::ProcessClone
// Adapted bodies: none
// A byte match shows that this source and recipe produce the checked code; it does not verify the
// community names or that the original source looked like this.
#include "NiMultiTargetTransformController.h"


// Not compared: defined so that the compiler emits the vftable and, beside it, the
// deleting destructor that is compared (cookbook rule 14).
NiMultiTargetTransformController::NiMultiTargetTransformController()
{
}

// RVA 0xf5de10, 5 bytes
std::uint16_t NiMultiTargetTransformController::GetInterpolatorCount() const
{
    return m_count;
}

// RVA 0xf5de20, 16 bytes
const char* NiMultiTargetTransformController::GetInterpolatorID(std::uint16_t a_index)
{
    return m_entryPtrs[a_index]->name;
}

// RVA 0xf5e280, 108 bytes: every entry is told the same time range.
void NiMultiTargetTransformController::GuaranteeTimeRange(float a_startTime, float a_endTime)
{
    for (std::uint16_t i = 0; i < m_count; ++i) {
        m_entries[i].GuaranteeTimeRange(a_startTime, a_endTime);
    }
}
